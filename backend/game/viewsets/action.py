import json
import math
import traceback
from typing import Dict, Iterable, List, Optional, Set, Tuple
from core.models.announcement import Announcement, AnnouncementType

from core.models.team import Team
from django.db import transaction
from django.db.models.functions import Now
from django.shortcuts import get_object_or_404
from django.utils import timezone
from game.actions import GAME_ACTIONS
from game.actions.actionBase import ActionInterface, ActionResult
from game.actions.common import (ActionFailed, MessageBuilder)
from game.actions.researchFinish import ActionResearchFinish
from game.actions.researchStart import ActionResearchStart
from game.entities import DieId, Entities, Entity, dieName
from game.gameGlue import stateDeserialize, stateSerialize
from game.models import (DbAction, DbDelayedEffect, DbEntities, DbInteraction,
                         DbState, DbSticker, DbTask, DbTaskAssignment, DbTurn,
                         InteractionType, StickerType)
from django.db.models import Q, Count
from game.state import StateModel
from game.viewsets.permissions import IsOrg
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import APIException
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from game.viewsets.stickers import DbStickerSerializer

StickerId = Tuple[Team, Entity]

class MulticommitError(APIException):
    status_code = 409
    default_detail = "Akce již byla uzavřena. Není možné ji uzavřít znovu."
    default_code = 'conflict'

class InitiateSerializer(serializers.Serializer):
    action = serializers.ChoiceField(list(GAME_ACTIONS.keys()))
    args = serializers.JSONField()

class CommitSerializer(serializers.Serializer):
    throws = serializers.IntegerField()
    dots = serializers.IntegerField()

class ActionViewSet(viewsets.ViewSet):
    permission_classes = (IsAuthenticated, IsOrg)

    @staticmethod
    def _handleExtraCommitSteps(action):
        team = None
        try:
            if hasattr(action.args, "team"):
                team = Team.objects.get(id=action.args.team.id)
        except Team.DoesNotExist:
            pass
        if isinstance(action, ActionResearchStart):
            if action.args.task is None:
                return
            try:
                task = DbTask.objects.get(id=action.args.task)
            except DbTask.DoesNotExist:
                return
            DbTaskAssignment.objects.create(
                team=team,
                task=task,
                techId=action.args.tech.id,
            )
            return
        if isinstance(action, ActionResearchFinish):
            for t in DbTaskAssignment.objects.filter(team=team, techId=action.args.tech.id, finishedAt=None):
                t.finishedAt = Now()
                t.save()

    @staticmethod
    def constructAction(actionType, args, entities, state):
        Action = GAME_ACTIONS[actionType]
        argsObj = stateDeserialize(Action.argument, args, entities)
        action = Action.action()
        action._state = state
        action._entities = entities
        action._generalArgs = argsObj
        return action

    @staticmethod
    def dbStoreInteraction(dbAction, dbState, interactionType, user, state, action):
        interaction = DbInteraction(
            phase=interactionType,
            action=dbAction,
            author=user,
            actionObject=stateSerialize(action)
        )
        interaction.save()
        dbState.updateFromIr(state)
        dbState.action = interaction
        dbState.save()

        if action.description and len(action.description) > 0:
            dbAction.description = action.description
            dbAction.save()

    @staticmethod
    def addResultNotifications(result: ActionResult) -> None:
        now = timezone.now()
        for t, messages in result.notifications.items():
            team = Team.objects.get(pk=t)
            for message in messages:
                a = Announcement.create(
                    author=None,
                    appearDateTime=now,
                    type=AnnouncementType.game,
                    content=message)
                a.teams.add(team)

    @staticmethod
    def _computeStickers(prev: StateModel, post: StateModel) -> Set[StickerId]:
        stickers = {t: s.collectStickerEntitySet() for t, s in post.teamStates.items()}
        for t, s in prev.teamStates.items():
            stickers[t].difference_update(s.collectStickerEntitySet())
        res = set()
        for t, sSet in stickers.items():
            for e in sSet:
                res.add((t, e))
        return res

    @staticmethod
    def _awardStickers(stickerIds: Iterable[str]) -> List[DbSticker]:
        if len(stickerIds) > 0:
            entRevision = DbEntities.objects.latest().id

        awardedStickers = []
        for t, s in stickerIds:
            team = Team.objects.get(pk=t.id)
            if s.id.startswith("tec-") and not DbSticker.objects.filter(entityId=s).exists():
                # The team is first, let's give him a special sticker
                firstTech = DbSticker.objects.create(team=team, entityId=s.id,
                    entityRevision=entRevision, type=StickerType.techFirst)
                awardedStickers.append(firstTech)
            if s.id.startswith("tec-"):
                smallTech = DbSticker.objects.create(team=team, entityId=s.id,
                    entityRevision=entRevision, type=StickerType.techSmall)
                awardedStickers.append(smallTech)
            model = DbSticker.objects.create(team=team, entityId=s.id,
                    entityRevision=entRevision, type=StickerType.regular)
            awardedStickers.append(model)
        return awardedStickers


    @staticmethod
    def _markDelayedEffect(dbAction: DbAction, delayedRequirements):
        now = timezone.now()
        try:
            turnObject = DbTurn.objects.getActiveTurn()
        except DbTurn.DoesNotExist:
            raise RuntimeError("Ještě nebyla započata hra, nemůžu provádět odložené efekty.") from None
        effectTime = now + timezone.timedelta(seconds=int(delayedRequirements))
        while turnObject.shouldStartAt < effectTime:
            turnObject = turnObject.next
            if turnObject is None:
                raise RuntimeError("Odložený efekt akce je moc daleko - nemám dost kol.")
        turnObject = turnObject.prev
        targetTurnId = turnObject.id
        targetOffset = (effectTime - turnObject.shouldStartAt).total_seconds()

        team = Team.objects.get(pk=dbAction.args.get("team"))

        effect = DbDelayedEffect.objects.create(round=targetTurnId, target=targetOffset,
                                                action=dbAction, team=team)
        return effect

    @staticmethod
    @transaction.atomic
    def performDelayedEffect(effect: DbDelayedEffect) -> None:
        Self = ActionViewSet

        dbAction = effect.action
        _, entities = DbEntities.objects.get_revision(dbAction.entitiesRevision)

        dbState = DbState.objects.latest()
        state = dbState.toIr()
        sourceState = dbState.toIr()

        dbInteraction = dbAction.lastInteraction
        action = dbInteraction.getActionIr(entities, state)

        result = action.applyDelayedEffect()
        Self.dbStoreInteraction(dbAction, dbState, InteractionType.delayed,
                                None, action.state, action)

        Self.addResultNotifications(result)
        stickers = Self._computeStickers(sourceState, state)

        effect.stickers = list(stickers)
        effect.performed = True
        effect.save()

    @staticmethod
    def awardDelayedEffect(effect: DbDelayedEffect) -> Tuple[ActionResult, List[StickerId]]:
        Self = ActionViewSet

        dbAction = effect.action
        _, entities = DbEntities.objects.get_revision(dbAction.entitiesRevision)

        dbState = DbState.objects.latest()
        state = dbState.toIr()
        sourceState = dbState.toIr()

        dbInteraction = dbAction.lastInteraction
        action = dbInteraction.getActionIr(entities, state)

        result = action.applyDelayedReward()
        Self.dbStoreInteraction(dbAction, dbState, InteractionType.delayedReward,
                                None, action.state, action)
        gainedStickers = Self._computeStickers(sourceState, state)
        effect.stickers = effect.stickers + list(gainedStickers)
        effect.withdrawn = True
        effect.save()

        Self._awardStickers(effect.stickers)

        Self.addResultNotifications(result)
        return result, gainedStickers

    @staticmethod
    def _previewMessage(initiateResult: ActionResult, dice: Tuple[Set[DieId], int],
            commitResult: ActionResult, stickers: Iterable[StickerId], delayed: int) -> str:
        b = MessageBuilder()
        b.add("## Předpoklady")
        b.add(initiateResult.message)
        if dice[1]:
            with b.startList(f"Je třeba hodit {dice[1]} na jedné z:") as addDice:
                for d in dice[0]:
                    dieName(d)
        else:
            b.add("Akce nevyžaduje házení kostkou")

        b.add("## Efekty")
        b.add(commitResult.message)
        with b.startList("Budou vydány samolepky:") as addLine:
            for t, e in stickers:
                addLine(f"samolepka {e.name} pro tým {t.name}")
        if delayed > 0:
            b.add(f"**Akce má odložený efekt za {round(delayed / 60)} minut**")
        return b.message

    @staticmethod
    def _initiateMessage(initiateResult: ActionResult, dice: Tuple[Set[DieId], int],
            commitResult: Optional[ActionResult], stickers: Iterable[StickerId],
            delayedEffect: Optional[DbDelayedEffect]) -> str:
        b = MessageBuilder()
        b.add("## Předpoklady")
        b.add(initiateResult.message)
        if dice[1]:
            with b.startList(f"Je třeba hodit {dice[1]} na jedné z:") as addDice:
                for d in dice[0]:
                    addDice(dieName(d))
        else:
            b.add("Akce nevyžaduje házení kostkou")

        if commitResult is not None:
            b.add("## Efekty")
            b.add(commitResult.message)
            with b.startList("Budou vydány samolepky:") as addLine:
                for t, e in stickers:
                    addLine(f"samolepka {e.name} pro tým {t.name}")
        if delayedEffect is not None:
            b.add(f"""**Akce má odložený efekt v kole {delayedEffect.round} a
                    {round(delayedEffect.target / 60)} minut.
                    Vyzvedává se kódem: {delayedEffect.slug}**""")
        return b.message

    @staticmethod
    def _commitMessage(commitResult: ActionResult,
                         delayedEffect: Optional[DbDelayedEffect]) -> str:
        b = MessageBuilder()

        b.add("## Efekty")
        b.add(commitResult.message)

        if delayedEffect is not None:
            b.add(f"""**Akce má odložený efekt v kole {delayedEffect.round} a
                    {round(delayedEffect.target / 60)} minut.
                    Vyzvedává se kódem: {delayedEffect.slug}**""")
        return b.message

    @staticmethod
    def _actionFailedResponse(e: ActionFailed) -> Response:
        return Response(data={
            "success": False,
            "message": f"Akci nelze zadat: \n\n{e}"
        })

    @staticmethod
    def _unexpectedErrorResponse(e: Exception, traceback: str) -> Response:
        return Response(data={
            "success": False,
            "message": f"Nastala chyba, kterou je třeba zahlásit Maarovi: \n\n{e}\n\n```\n{traceback}\n```"
        })

    @staticmethod
    def _ensureGameIsRunning(actionName) -> None:
        if actionName in ["GodModeAction"]:
            return
        try:
            DbTurn.objects.getActiveTurn()
        except DbTurn.DoesNotExist:
            raise ActionFailed("Hra neběží. Není možné zadávat akce.") from None

    @action(methods=["POST"], detail=False)
    def dry(self, request):
        deserializer = InitiateSerializer(data=request.data)
        deserializer.is_valid(raise_exception=True)
        data = deserializer.validated_data

        _, entities = DbEntities.objects.get_revision()
        dbState = DbState.objects.latest()
        state = dbState.toIr()
        sourceState = dbState.toIr()

        try:
            self._ensureGameIsRunning(data["action"])
            action = self.constructAction(data["action"], data["args"], entities, state)

            initiateResult = action.applyInitiate()

            requiresDice = action.diceRequirements()[1] != 0
            commitResult = action.applyCommit(1 if requiresDice else 0,
                                              action.diceRequirements()[1])
            delayed = action.requiresDelayedEffect()
            stickers = self._computeStickers(sourceState, action._state)

            return Response(data={
                "success": True,
                "expected": initiateResult.expected and \
                            (commitResult is None or commitResult.expected),
                "message": self._previewMessage(initiateResult, action.diceRequirements(),
                    commitResult, stickers, delayed)
            })
        except ActionFailed as e:
            return self._actionFailedResponse(e)
        except Exception as e:
            tb = traceback.format_exc()
            return self._unexpectedErrorResponse(e, tb)

    @action(methods=["POST"], detail=False)
    def initiate(self, request):
        deserializer = InitiateSerializer(data=request.data)
        deserializer.is_valid(raise_exception=True)
        data = deserializer.validated_data

        try:
            with transaction.atomic():
                self._ensureGameIsRunning(data["action"])

                entityRevision, entities = DbEntities.objects.get_revision()
                dbState = DbState.objects.latest()
                state = dbState.toIr()
                sourceState = dbState.toIr()
                dryState = dbState.toIr()

                action = self.constructAction(data["action"], data["args"], entities, state)
                dryAction = self.constructAction(data["action"], data["args"], entities, dryState)

                initiateResult = action.applyInitiate()
                dryAction.applyInitiate()
                diceReq = action.diceRequirements()

                dbAction = DbAction(
                        actionType=data["action"],
                        entitiesRevision=entityRevision,
                        args=stateSerialize(action.args))
                dbAction.save()
                self.dbStoreInteraction(dbAction, dbState,
                    InteractionType.initiate, request.user, state, action)

                commitResult = None
                delayedEffect = None
                gainedStickers = set()
                awardedStickers = []
                if diceReq[1] == 0:
                    commitResult = action.applyCommit(0, 0)
                    self.dbStoreInteraction(dbAction, dbState,
                        InteractionType.commit,request.user, state, action)
                    self._handleExtraCommitSteps(action)
                    gainedStickers = self._computeStickers(sourceState, state)
                    delayedRequirements = action.requiresDelayedEffect()
                    if delayedRequirements:
                        delayedEffect = self._markDelayedEffect(dbAction, delayedRequirements)
                else:
                    # Let's perform the commit on dryState as some validation
                    # happens in commit /o\
                    dryAction.applyCommit()

                awardedStickers = self._awardStickers(gainedStickers)
                self.addResultNotifications(initiateResult)
                if commitResult is not None:
                    self.addResultNotifications(commitResult)

                return Response(data={
                    "success": True,
                    "expected": initiateResult.expected and \
                                (commitResult is None or commitResult.expected),
                    "action": dbAction.id,
                    "committed": commitResult is not None,
                    "message": self._initiateMessage(initiateResult, diceReq,
                                    commitResult, gainedStickers, delayedEffect),
                    "stickers": DbStickerSerializer(awardedStickers, many=True).data,
                    "voucher": delayedEffect.slug if delayedEffect is not None else None
                })
        except ActionFailed as e:
            return self._actionFailedResponse(e)
        except Exception as e:
            tb = traceback.format_exc()
            return self._unexpectedErrorResponse(e, tb)

    @action(methods=["POST", "GET"], detail=True)
    def commit(self, request, pk=True):
        dbAction = get_object_or_404(DbAction, pk=pk)
        self._ensureGameIsRunning(dbAction.actionType)

        _, entities = DbEntities.objects.get_revision(dbAction.entitiesRevision)

        dbState = DbState.objects.latest()
        state = dbState.toIr()
        sourceState = dbState.toIr()

        dbInteraction = dbAction.lastInteraction
        action = dbInteraction.getActionIr(entities, state)

        diceReq = action.diceRequirements()

        if request.method == "GET":
            return Response({
                "requiredDots": diceReq[1],
                "allowedDice": list(diceReq[0]),
                "throwCost": action.throwCost(),
                "description": dbAction.description,
                "team": action.team.id
            })

        if dbAction.interactions.count() != 1:
            raise MulticommitError()

        try:
            with transaction.atomic():
                deserializer = CommitSerializer(data=request.data)
                deserializer.is_valid(raise_exception=True)
                params = deserializer.validated_data

                commitResult = action.applyCommit(params["throws"], params["dots"])
                self.dbStoreInteraction(dbAction, dbState,
                    InteractionType.commit,request.user, state, action)
                self._handleExtraCommitSteps(action)
                gainedStickers = self._computeStickers(sourceState, state)
                delayedRequirements = action.requiresDelayedEffect()
                if delayedRequirements:
                    delayedEffect = self._markDelayedEffect(dbAction, delayedRequirements)
                else:
                    delayedEffect = None
                awardedStickers = self._awardStickers(gainedStickers)
                self.addResultNotifications(commitResult)


                return Response(data={
                    "success": True,
                    "expected": commitResult.expected,
                    "message": self._commitMessage(commitResult, delayedEffect),
                    "stickers": DbStickerSerializer(awardedStickers, many=True).data,
                    "voucher": delayedEffect.slug if delayedEffect is not None else None
                })
        except ActionFailed as e:
            return self._actionFailedResponse(e)
        except Exception as e:
            tb = traceback.format_exc()
            return self._unexpectedErrorResponse(e, tb)

    @action(methods=["POST"], detail=True)
    @transaction.atomic()
    def cancel(self, request, pk=True):
        dbAction = get_object_or_404(DbAction, pk=pk)
        _, entities = DbEntities.objects.get_revision(dbAction.entitiesRevision)

        dbState = DbState.objects.latest()
        state = dbState.toIr()

        dbInteraction = dbAction.lastInteraction
        action = dbInteraction.getActionIr(entities, state)

        try:
            with transaction.atomic():
                result = action.revertInitiate()
            self.dbStoreInteraction(dbAction, dbState, InteractionType.cancel,
                request.user, state, action)
            return Response({
                "success": True,
                "message": f"## Akce zrušena\n\n{result.message}"
            })
        except ActionFailed as e:
            return self._actionFailedResponse(e)
        except Exception as e:
            tb = traceback.format_exc()
            return self._unexpectedErrorResponse(e, tb)


    @action(methods=["GET"], detail=False)
    @transaction.atomic()
    def unfinished(self, request):
        unfinishedInteractions = DbInteraction.objects \
            .filter(phase=InteractionType.initiate, author=request.user) \
            .annotate(interaction_count=Count("action__interactions")) \
            .filter(interaction_count=1)
        unfinishedActions = DbAction.objects \
            .filter(interactions__in=unfinishedInteractions).distinct()
        return Response([{
                "id": x.id,
                "description": x.description
            } for x in unfinishedActions])

