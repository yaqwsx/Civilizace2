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
from game.actions.actionBase import ActionResult, InitiateResult
from game.actions.common import (ActionCost, ActionException,
                                 CancelationResult, MessageBuilder)
from game.actions.researchFinish import ActionResearchFinish
from game.actions.researchStart import ActionResearchStart
from game.entities import THROW_COST, Entities, Entity
from game.gameGlue import stateDeserialize, stateSerialize
from game.models import (DbAction, DbDelayedEffect, DbEntities, DbInteraction,
                         DbState, DbSticker, DbTask, DbTaskAssignment, DbTurn,
                         InteractionType, StickerType)
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

class NotEnoughWork(APIException):
    status_code = 409
    default_detail = "Tým neměl dostatek práce, opakujte."
    default_code = 'not_enough_work'

def actionPreviewMessage(cost: ActionCost, initiate: InitiateResult,
                        action: Optional[ActionResult],
                        stickers: Iterable[StickerId]) -> str:
    b = MessageBuilder()
    if action is None or not initiate.succeeded:
        b.add("Akce stojí:")
        b.addEntityDict("", cost.materials)
        b.addEntityDict("", cost.productions)
        b.add(cost.formatDice())
        b.addEntityDict("**Avšak týmu chybí:**", initiate.missingProductions)
        b.add("**Akci nelze začít**")
        return b.message

    b.add("### Předpoklady")
    b.addEntityDict("Akce stojí:", cost.productions)
    b.addEntityDict("**Od týmu vyberte:**", cost.materials)
    b.add(cost.formatDice())

    b.add("### Efekt akce:")
    b.add(action.message)
    b.addEntityDict("Tým dostane:", action.productions)
    b.addEntityDict("Týmu vydáte:", action.materials)
    with b.startList("Tým dostane samolepky:") as addLine:
        for t, e in stickers:
            addLine(f"samolepka {e.name} pro tým {t.name}")

    if cost.postpone > 0:
        b.add(f"**Akce má odložený efekt za {round(cost.postpone / 60)} minut**")
    return b.message

def actionInitiateMessage(cost: ActionCost, initiate: InitiateResult,
                          action: Optional[ActionResult],
                          stickers: Iterable[StickerId],
                          delayedEffect: Optional[DbDelayedEffect]) -> str:
    b = MessageBuilder()
    if not initiate.succeeded:
        b.add("Akce stojí:")
        b.addEntityDict("", cost.materials)
        b.addEntityDict("", cost.productions)
        b.add(cost.formatDice())
        b.addEntityDict("**Avšak týmu chybí:**", initiate.missingProductions)
        b.add("**Akci nelze začít**")
        return b.message

    b.add("### Cena")
    b.addEntityDict("Týmu bylo odebráno:", cost.productions)
    b.addEntityDict("**Od týmu vyberte:**", cost.materials)
    b.add(cost.formatDice())

    if action is not None:
        b.add("### Efekt akce:")
        b.add(action.message)
        b.addEntityDict("Tým dostane:", action.productions)
        b.addEntityDict("Týmu vydáte:", action.materials)
        with b.startList("Tým dostane samolepky:") as addLine:
            for t, e in stickers:
                addLine(f"samolepka {e.name} pro tým {t.name}")

    if delayedEffect is not None:
        b.add(f"""**Akce má odložený efekt v kole {delayedEffect.round} a
                {round(delayedEffect.target / 60)} minut.
                Vyzvedává se kódem: {delayedEffect.slug}**""")
    elif cost.postpone > 0:
        b.add(f"**Akce má odložený efekt za {round(cost.postpone / 60)} minut**")
    return b.message

def actionCommitMessage(action: ActionResult,
                        stickers: Iterable[StickerId],
                        delayedEffect: Optional[DbDelayedEffect]) -> str:
    b = MessageBuilder()
    b.add("### Efekt akce:")
    b.add(action.message)
    b.addEntityDict("Tým dostal:", action.productions)
    b.addEntityDict("Týmu vydejte:", action.materials)
    with b.startList("Tým dostane samolepky:") as addLine:
        for t, e in stickers:
            addLine(f"samolepka {e.name} pro tým {t.name}")

    if delayedEffect is not None:
        b.add(f"""**Akce má odložený efekt v kole {delayedEffect.round} a
                  {round(delayedEffect.target / 60)} minut.
                  Vyzvedává se kódem: {delayedEffect.slug}**""")
    return b.message

def actionCancelMessage(result: CancelationResult) -> str:
    b = MessageBuilder()
    b.add("### Akce byla zrušena, vraťte týmu:")
    b.addEntityDict("Tým dostal:", result.materials)
    return b.message

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
            team = Team.objects.get(id=action.team.id)
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
        args = stateDeserialize(Action.argument, args, entities)
        action = Action.action(entities=entities, state=state, args=args)
        return action

    @staticmethod
    def dbStoreInteraction(dbAction, dbState, interactionType, user, state):
        interaction = DbInteraction(
            phase=interactionType,
            action=dbAction,
            author=user
        )
        interaction.save()
        dbState.updateFromIr(state)
        dbState.action = interaction
        dbState.save()

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
            print(t)
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
    def _markDelayedEffect(dbAction: DbAction, cost: ActionCost):
        now = timezone.now()
        try:
            turnObject = DbTurn.objects.getActiveTurn()
        except DbTurn.DoesNotExist:
            raise RuntimeError("Ještě nebyla započata hra, nemůžu provádět odložené efekty.") from None
        effectTime = now + timezone.timedelta(seconds=cost.postpone)
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

        action = Self.constructAction(dbAction.actionType, dbAction.args, entities, state)
        result = action.delayed()
        Self.dbStoreInteraction(dbAction, dbState, InteractionType.delayed,
                                None, action.state)
        addResultNotifications(result)
        stickers = Self._computeStickers(sourceState, state)

        effect.result = stateSerialize(result)
        effect.stickers = list(stickers)
        effect.save()

    @staticmethod
    def awardDelayedEffect(effect: DbDelayedEffect) -> Tuple[ActionResult, List[StickerId]]:
        Self = ActionViewSet

        dbAction = effect.action
        _, entities = DbEntities.objects.get_revision(dbAction.entitiesRevision)
        dbState = DbState.objects.latest()
        state = dbState.toIr()

        action = Self.constructAction(dbAction.actionType, dbAction.args, entities, state)
        result = stateDeserialize(ActionResult, effect.result, entities)

        action.commitReward(result.productions)

        Self.dbStoreInteraction(dbAction, dbState, InteractionType.delayedReward,
                                None, action.state)

        return result, effect.stickers


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
            action = self.constructAction(data["action"], data["args"], entities, state)
            cost = action.cost()
            initiateResult = action.initiate(cost)
            if not initiateResult.succeeded:
                return Response(data={
                        "success": False,
                        "message": actionPreviewMessage(cost, initiateResult, None, [])
                    })
            result = action.commit()
            stickers = self._computeStickers(sourceState, state)
            return Response(data={
                "success": result.succeeded,
                "message": actionPreviewMessage(cost, initiateResult, result, stickers)
            })
        except ActionException as e:
            return Response(data={
                "success": False,
                "message": f"Nesplněny prerekvizity akce: \n\n{e}"
            })
        except Exception as e:
            tb = traceback.format_exc()
            return Response(data={
                "success": False,
                "message": f"Nastala chyba, kterou je třeba zahlásit Maarovi: \n\n{e}\n\n```\n{tb}\n```"
            })

    @action(methods=["POST"], detail=False)
    def initiate(self, request):
        deserializer = InitiateSerializer(data=request.data)
        deserializer.is_valid(raise_exception=True)
        data = deserializer.validated_data

        try:
            with transaction.atomic():
                entityRevision, entities = DbEntities.objects.get_revision()
                dbState = DbState.objects.latest()
                state = dbState.toIr()
                sourceState = dbState.toIr()
                dryState = dbState.toIr()

                action = self.constructAction(data["action"], data["args"], entities, state)

                cost = action.cost()
                initiateResult = action.initiate(cost)
                if not initiateResult.succeeded:
                    return Response(data={
                            "success": False,
                            "message": actionPreviewMessage(cost, initiateResult, None, [])
                        })

                dbAction = DbAction(
                        actionType=data["action"], entitiesRevision=entityRevision,
                        args=stateSerialize(action.args), cost=stateSerialize(cost))
                dbAction.save()
                self.dbStoreInteraction(dbAction, dbState, InteractionType.initiate, request.user, state)

                result = None
                effect = None
                stickers = set()
                awardedStickers = []
                if cost.requiredDots == 0:
                    result = action.commit(cost)
                    addResultNotifications(result)
                    if result.succeeded:
                        action.commitReward(result.productions)
                    self.dbStoreInteraction(dbAction, dbState, InteractionType.commit, request.user, state)
                    self._handleExtraCommitSteps(action)
                    stickers = self._computeStickers(sourceState, state)
                    awardedStickers = self._awardStickers(stickers)
                    if cost.postpone > 0:
                        effect = self._markDelayedEffect(dbAction, cost)
                else:
                    # Let's perform the commit on dryState since all the
                    # validation happens in commit /o\
                    dryAction = self.constructAction(data["action"], data["args"], entities, dryState)
                    dryAction.initiate(cost)
                    dryAction.commit(cost)
                return Response(data={
                    "success": result is None or result.succeeded,
                    "action": dbAction.id,
                    "committed": result is not None,
                    "message": actionInitiateMessage(cost, initiateResult, result, stickers, effect),
                    "stickers": DbStickerSerializer(awardedStickers, many=True).data,
                    "voucher": effect.slug if effect is not None else None
                })
        except ActionException as e:
            return Response(data={
                "success": False,
                "message": f"Nesplněny prerekvizity akce: \n\n{e}",
                "stickers": [],
                "voucher": None
            })
        except Exception as e:
            tb = traceback.format_exc()
            return Response(data={
                "success": False,
                "message": f"Nastala chyba, kterou je třeba zahlásit Maarovi: \n\n{e}\n\n```\n{tb}\n```",
                "stickers": [],
                "voucher": None
            })

    @action(methods=["POST", "GET"], detail=True)
    def commit(self, request, pk=True):
        dbAction = get_object_or_404(DbAction, pk=pk)
        _, entities = DbEntities.objects.get_revision(dbAction.entitiesRevision)

        cost = stateDeserialize(ActionCost, dbAction.cost, entities)
        if request.method == "GET":
            return Response({
                "requiredDots": cost.requiredDots,
                "allowedDice": list(cost.allowedDice)
            })

        if dbAction.interactions.count() != 1:
            raise MulticommitError()

        try:
            with transaction.atomic():
                deserializer = CommitSerializer(data=request.data)
                deserializer.is_valid(raise_exception=True)
                params = deserializer.validated_data

                dbState = DbState.objects.latest()
                state = dbState.toIr()
                sourceState = dbState.toIr()

                action = self.constructAction(dbAction.actionType, dbAction.args, entities, state)

                workCommitSucc = action.payWork(params["throws"] * THROW_COST)
                if workCommitSucc and params["dots"] >= cost.requiredDots:
                    result = action.commit()
                    addResultNotifications(result)
                    if result.succeeded:
                        action.commitReward(result.productions)
                    stickers = self._computeStickers(sourceState, state)
                    self.dbStoreInteraction(dbAction, dbState, InteractionType.commit, request.user, state)
                    self._handleExtraCommitSteps(action)
                    awardedStickers = self._awardStickers(stickers)
                    effect = None
                    if result.succeeded and cost.postpone > 0:
                        effect = self._markDelayedEffect(dbAction, cost)
                    return Response({
                        "success": result.succeeded,
                        "message": actionCommitMessage(result, stickers, effect),
                        "stickers": DbStickerSerializer(awardedStickers, many=True).data,
                        "voucher": effect.slug if effect is not None else None
                    })
                else:
                    # There wasn't enough dots, abandon
                    result = action.abandon(cost)
                    self.dbStoreInteraction(dbAction, dbState, InteractionType.abandon, request.user, state)
                    if workCommitSucc:
                        message = "# Tým nenaházel dostatek\n\nTýmu se vrací pouze produkce a tým nic nezískává"
                    else:
                        message = "# Týmu došla práce (asi házel i na jiném stanovišti)\n\nTýmů se vrací pouze produkce a tým nic nezískává"
                    return Response({
                        "success": False,
                        "message": message,
                        "stickers": [],
                        "voucher": None
                    })
        except ActionException as e:
            result = action.cancel(cost)
            self.dbStoreInteraction(dbAction, dbState, InteractionType.cancel, request.user, state)

            return Response(data={
                "success": False,
                "message": f"Nesplněny prerekvizity akce: \n\n{e}\n\n{actionCancelMessage(cost, result)}",
                "stickers": [],
                "voucher": None
            })
        except Exception as e:
            tb = traceback.format_exc()

            result = action.cancel(cost)
            self.dbStoreInteraction(dbAction, dbState, InteractionType.cancel, request.user, state)

            return Response(data={
                "success": False,
                "message": f"Nastala chyba, kterou je třeba zahlásit Maarovi: \n\n{e}\n\n\n\n{actionCancelMessage(cost, result)}\n\n```\n{tb}\n```",
                "stickers": [],
                "voucher": None
            })

    @action(methods=["POST"], detail=True)
    @transaction.atomic()
    def cancel(self, request, pk=True):
        dbAction = get_object_or_404(DbAction, pk=pk)
        cost = stateDeserialize(ActionCost, dbAction.cost)
        if dbAction.interactions.count() != 1:
            raise MulticommitError()

        _, entities = DbEntities.objects.get_revision(dbAction.entitiesRevision)
        dbState = DbState.objects.latest()
        state = dbState.toIr()

        action = self.constructAction(dbAction.actionType, dbAction.args, entities, state)

        result = action.cancel()
        dbInitiate = DbInteraction(
            phase=InteractionType.cancel,
            action=dbAction,
            author=request.user)
        dbInitiate.save()
        dbState.updateFromIr(action.state)
        dbState.action = dbInitiate
        dbState.save()
        return Response({
            "success": True,
            "message": actionCancelMessage(cost, result)
        })
