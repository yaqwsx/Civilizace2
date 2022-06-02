from django.shortcuts import get_object_or_404
from django.db.models.functions import Now
from typing import Dict, Iterable, Optional, Set, Tuple
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework import serializers
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from game.actions.actionBase import ActionResult, InitiateResult
from game.actions.common import ActionCost, ActionException, CancelationResult, MessageBuilder
from game.actions.researchFinish import ActionResearchFinish
from game.actions.researchStart import ActionResearchStart
from game.entities import THROW_COST, Entities, Entity
from game.gameGlue import stateDeserialize, stateSerialize
from game.models import DbAction, DbEntities, DbInteraction, DbState, DbTask, DbTaskAssignment, InteractionType
from django.db import transaction
import traceback

from core.models.team import Team
from game.state import StateModel

from game.viewsets.permissions import IsOrg

from game.actions import GAME_ACTIONS

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
                        action: Optional[ActionResult], stickers: Iterable[StickerId]) -> str:
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
        b.add(f"**Akce má odložený efekt za {cost.postpone} divnojednotek**")
    return b.message

def actionInitiateMessage(cost: ActionCost, initiate: InitiateResult,
                          action: Optional[ActionResult], stickers: Iterable[StickerId]) -> str:
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

        if cost.postpone > 0:
            b.add(f"**Akce má odložený efekt za {cost.postpone} divnojednotek**")
    return b.message

def actionCommitMessage(cost: ActionCost, action: ActionResult, stickers: Iterable[StickerId]) -> str:
    b = MessageBuilder()
    b.add("### Efekt akce:")
    b.add(action.message)
    b.addEntityDict("Tým dostal:", action.productions)
    b.addEntityDict("Týmu vydejte:", action.materials)
    with b.startList("Tým dostane samolepky:") as addLine:
        for t, e in stickers:
            addLine(f"samolepka {e.name} pro tým {t.name}")

    if cost.postpone > 0:
        b.add(f"**Akce má odložený efekt za {cost.postpone} divnojednotek**")
    return b.message

def actionCancelMessage(result: CancelationResult) -> str:
    b = MessageBuilder()
    b.add("### Akce byla zrušena, vraťte týmu:")
    b.addEntityDict("Tým dostal:", result.materials)
    return b.message

class InitiateSerializer(serializers.Serializer):
    action = serializers.ChoiceField(list(GAME_ACTIONS.keys()))
    args = serializers.JSONField()

class CommitSerializer(serializers.Serializer):
    throws = serializers.IntegerField()
    dots = serializers.IntegerField()

class ActionViewSet(viewsets.ViewSet):
    permission_classes = (IsAuthenticated, IsOrg)

    def _handleExtraCommitSteps(self, action):
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

    def constructAction(self, actionType, args, entities, state):
        Action = GAME_ACTIONS[actionType]
        args = stateDeserialize(Action.argument, args, entities)
        action = Action.action(entities=entities, state=state, args=args)
        return action

    def dbStoreInteraction(self, dbAction, dbState, interactionType, user, state):
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
                        "message": actionPreviewMessage(cost, initiateResult, None)
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
                            "message": actionPreviewMessage(cost, initiateResult, None)
                        })

                dbAction = DbAction(
                        actionType=data["action"], entitiesRevision=entityRevision,
                        args=stateSerialize(action.args), cost=stateSerialize(cost))
                dbAction.save()
                self.dbStoreInteraction(dbAction, dbState, InteractionType.initiate, request.user, state)

                result = None
                stickers = set()
                if cost.requiredDots == 0:
                    result = action.commit(cost)
                    if result.succeeded:
                        action.commitReward(result.productions)
                    self.dbStoreInteraction(dbAction, dbState, InteractionType.commit, request.user, state)
                    self._handleExtraCommitSteps(action)
                    stickers = self._computeStickers(sourceState, state)
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
                    "message": actionInitiateMessage(cost, initiateResult, result, stickers)
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
                    if result.succeeded:
                        action.commitReward(result.productions)
                    stickers = self._computeStickers(sourceState, state)
                    self.dbStoreInteraction(dbAction, dbState, InteractionType.commit, request.user, state)
                    self._handleExtraCommitSteps(action)
                    return Response({
                        "success": result.succeeded,
                        "message": actionCommitMessage(cost, result, stickers)
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
                        "message": message
                    })
        except ActionException as e:
            result = action.cancel(cost)
            self.dbStoreInteraction(dbAction, dbState, InteractionType.cancel, request.user, state)

            return Response(data={
                "success": False,
                "message": f"Nesplněny prerekvizity akce: \n\n{e}\n\n{actionCancelMessage(cost, result)}"
            })
        except Exception as e:
            tb = traceback.format_exc()

            result = action.cancel(cost)
            self.dbStoreInteraction(dbAction, dbState, InteractionType.cancel, request.user, state)

            return Response(data={
                "success": False,
                "message": f"Nastala chyba, kterou je třeba zahlásit Maarovi: \n\n{e}\n\n\n\n{actionCancelMessage(cost, result)}\n\n```\n{tb}\n```"
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
