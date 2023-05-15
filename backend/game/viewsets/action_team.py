import traceback
from typing import Iterable, Optional, Tuple

from django.db import transaction
from django.db.models import Count
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from core.models.team import Team
from game.actions import GAME_ACTIONS
from game.actions.actionBase import ActionResult, TeamInteractionActionBase
from game.actions.common import ActionFailed, MessageBuilder
from game.actions.researchFinish import ResearchFinishAction
from game.actions.researchStart import ResearchStartAction
from game.entities import Die, Entities
from game.entities import Team as TeamEntity
from game.gameGlue import serializeEntity, stateSerialize
from game.models import (DbAction, DbEntities, DbInteraction, DbState, DbTask,
                         DbTaskAssignment, GameTime, InteractionType)
from game.state import GameState
from game.viewsets.action_view_helper import (ActionViewHelper,
                                              UnexpectedActionTypeError,
                                              UnexpectedStateError)
from game.viewsets.permissions import IsOrg
from game.viewsets.stickers import DbStickerSerializer, Sticker


def checkInitiatePhase(interaction: InteractionType) -> None:
    if interaction == InteractionType.initiate:
        return
    elif interaction == InteractionType.revert:
        raise UnexpectedStateError("Akce již byla zrušena.")
    elif interaction == InteractionType.commit:
        raise UnexpectedStateError("Akce již byla uzavřena.")
    else:
        raise UnexpectedStateError(f"Neočekávaný stav akce ({interaction})")


class InitiateSerializer(serializers.Serializer):
    action = serializers.ChoiceField(list(id for (id, action) in GAME_ACTIONS.items() if issubclass(action.action, TeamInteractionActionBase)))
    args = serializers.JSONField()
    ignore_cost = serializers.BooleanField(default=False)  # type: ignore
    ignore_game_stop = serializers.BooleanField(default=False)  # type: ignore

class ThrowsSerializer(serializers.Serializer):
    throws = serializers.IntegerField(min_value=0)
    dots = serializers.IntegerField(min_value=0)
    ignore_throws = serializers.BooleanField(default=False)  # type: ignore

class DrySerializer(InitiateSerializer):
    ignore_throws = serializers.BooleanField(default=False)  # type: ignore

class TeamActionViewSet(viewsets.ViewSet):
    permission_classes = (IsAuthenticated, IsOrg)

    @staticmethod
    def _handleExtraCommitSteps(action):
        team = None
        try:
            if hasattr(action.args, "team"):
                team = Team.objects.get(id=action.args.team.id)
        except Team.DoesNotExist:
            pass
        if isinstance(action, ResearchStartAction):
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
        if isinstance(action, ResearchFinishAction):
            for t in DbTaskAssignment.objects.filter(team=team, techId=action.args.tech.id, finishedAt=None):
                t.finishedAt = timezone.now()
                t.save()

    @staticmethod
    def _previewDiceThrow(pointsCost: Optional[int]) -> str:
        if pointsCost is not None and pointsCost <= 0:
            return "Akce nevyžaduje házení kostkou"
        if pointsCost is None:
            return "Ignoruje se házení kostkou"
        return f"Je třeba hodit {pointsCost}"

    @staticmethod
    def _previewDryInteractionMessage(initiateInfo: str, pointsCost: Optional[int],
            commitResult: ActionResult, stickers: Iterable[Sticker],
            team: Optional[TeamEntity], entities: Entities, state: GameState) -> str:
        b = MessageBuilder()
        b.add("## Předpoklady")
        b.add(initiateInfo)

        b.add(TeamActionViewSet._previewDiceThrow(pointsCost))

        b.add("## Efekty")
        b.add(commitResult.message)
        with b.startList("Budou vydány samolepky:") as addLine:
            for t, e in stickers:
                addLine(f"samolepka {e.name} pro tým {t.name}")

        for scheduled in commitResult.scheduledActions:
            b += ActionViewHelper._previewScheduledAction(scheduled, team=team, entities=entities, state=state)

        return b.message

    @action(methods=["POST"], detail=False)
    def dry(self, request: Request) -> Response:
        deserializer = DrySerializer(data=request.data)
        deserializer.is_valid(raise_exception=True)
        data = deserializer.validated_data

        ignoreGameStop = request.user.is_superuser and data["ignore_game_stop"]
        ignoreCost = request.user.is_superuser and data["ignore_cost"]
        ignoreThrows = request.user.is_superuser and data["ignore_throws"]

        _, entities = DbEntities.objects.get_revision()
        dbState = DbState.objects.latest()
        state = dbState.toIr()
        sourceState = dbState.toIr()

        try:
            if not ignoreGameStop:
                ActionViewHelper._ensureGameIsRunning(data["action"])

            action = ActionViewHelper.constructAction(data["action"], data["args"], entities, state)
            if not isinstance(action, TeamInteractionActionBase):
                raise UnexpectedActionTypeError(action, TeamInteractionActionBase)

            initiateInfo = action.applyInitiate(ignore_cost=ignoreCost)
            commitResult = action.commitSuccess()

            # Check if the game started
            _ = GameTime.getNearestTime() if len(commitResult.scheduledActions) > 0 else None

            stickers = ActionViewHelper._computeStickersDiff(orig=sourceState, new=action.state)

            pointsCost = action.pointsCost() if not ignoreThrows else None
            message = TeamActionViewSet._previewDryInteractionMessage(initiateInfo, pointsCost,
                    commitResult, stickers, team=action.args.team, entities=action.entities, state=action.state)

            return Response(data={
                "success": True,
                "expected": commitResult.expected,
                "message": message,
            })
        except ActionFailed as e:
            return ActionViewHelper._actionFailedResponse(e)
        except Exception as e:
            tb = traceback.format_exc()
            return ActionViewHelper._unexpectedErrorResponse(e, tb)

    @action(methods=["POST"], detail=False)
    @transaction.atomic()
    def initiate(self, request: Request) -> Response:
        deserializer = InitiateSerializer(data=request.data)
        deserializer.is_valid(raise_exception=True)
        data = deserializer.validated_data

        ignoreGameStop = request.user.is_superuser and data["ignore_game_stop"]
        ignoreCost = request.user.is_superuser and data["ignore_cost"]

        try:
            if not ignoreGameStop:
                ActionViewHelper._ensureGameIsRunning(data["action"])

            entityRevision, entities = DbEntities.objects.get_revision()
            dbState = DbState.objects.latest()
            state = dbState.toIr()
            sourceState = dbState.toIr()
            dryState = dbState.toIr()

            action = ActionViewHelper.constructAction(data["action"], data["args"], entities, state)
            dryAction = ActionViewHelper.constructAction(data["action"], data["args"], entities, dryState)
            if not isinstance(action, TeamInteractionActionBase):
                raise UnexpectedActionTypeError(action, TeamInteractionActionBase)
            if not isinstance(dryAction, TeamInteractionActionBase):
                raise UnexpectedActionTypeError(dryAction, TeamInteractionActionBase)

            initiateInfo = action.applyInitiate(ignore_cost=ignoreCost)
            dryAction.applyInitiate(ignore_cost=ignoreCost)
            pointsCost = action.pointsCost()

            dbAction = DbAction.objects.create(
                    actionType=data["action"],
                    entitiesRevision=entityRevision,
                    args=stateSerialize(action.args))
            ActionViewHelper.dbStoreInteraction(dbAction, dbState,
                InteractionType.initiate, request.user, state, action)

            if pointsCost != 0:
                # Let's perform the commit on dryState as some validation
                # happens in commit /o\
                dryAction.commitSuccess()

                return Response(data={
                    "success": True,
                    "expected": True,
                    "action": dbAction.id,
                    "committed": False,
                    "message": initiateInfo,
                })

            commitResult = action.commitThrows(throws=0, dots=0)
            ActionViewHelper.dbStoreInteraction(dbAction, dbState,
                InteractionType.commit, request.user, state, action)

            TeamActionViewSet._handleExtraCommitSteps(action)

            gainedStickers = ActionViewHelper._computeStickersDiff(orig=sourceState, new=state)
            ActionViewHelper._markMapDiff(sourceState, state)

            scheduled = [ActionViewHelper._dbScheduleAction(scheduledAction, source=dbAction, author=request.user)
                         for scheduledAction in commitResult.scheduledActions]

            awardedStickers = ActionViewHelper._awardStickers(gainedStickers)
            ActionViewHelper.addResultNotifications(commitResult)

            msgBuilder = MessageBuilder(message=initiateInfo)
            msgBuilder += ActionViewHelper._commitMessage(commitResult, scheduled)

            return Response(data={
                "success": True,
                "expected": commitResult.expected,
                "action": dbAction.id,
                "committed": True,
                "message": msgBuilder.message,
                "stickers": DbStickerSerializer(awardedStickers, many=True).data,
            })
        except ActionFailed as e:
            return ActionViewHelper._actionFailedResponse(e)
        except Exception as e:
            tb = traceback.format_exc()
            return ActionViewHelper._unexpectedErrorResponse(e, tb)

    @action(methods=["POST", "GET"], detail=True)
    @transaction.atomic()
    def commit(self, request: Request, pk=True) -> Response:
        dbAction = get_object_or_404(DbAction, pk=pk)

        _, entities = DbEntities.objects.get_revision(dbAction.entitiesRevision)

        dbState = DbState.objects.latest()
        state = dbState.toIr()
        sourceState = dbState.toIr()

        dbInteraction = dbAction.lastInteraction()
        checkInitiatePhase(dbInteraction.phase)

        action = dbInteraction.getActionIr(entities, state)
        if not isinstance(action, TeamInteractionActionBase):
            raise UnexpectedActionTypeError(action, TeamInteractionActionBase)

        pointsCost = action.pointsCost()

        if request.method == "GET":
            return Response({
                "requiredDots": pointsCost,
                "throwCost": action.throwCost(),
                "description": dbAction.description,
                "team": action.args.team.id
            })

        # We want to allow finish action even when the game is not running
        # ActionViewHelper._ensureGameIsRunning(dbAction.actionType)
        try:
            deserializer = ThrowsSerializer(data=request.data)
            deserializer.is_valid(raise_exception=True)
            params = deserializer.validated_data
            assert params["throws"] >= 0, "ThrowsSerializer does not allow negative throws"
            assert params["dots"] >= 0, "ThrowsSerializer does not allow negative dots"

            ignoreThrows = request.user.is_superuser and params["ignore_throws"]

            if ignoreThrows:
                commitResult = action.commitSuccess()
            else:
                commitResult = action.commitThrows(throws=params["throws"], dots=params["dots"])
            ActionViewHelper.dbStoreInteraction(dbAction, dbState,
                InteractionType.commit,request.user, state, action)

            TeamActionViewSet._handleExtraCommitSteps(action)

            gainedStickers = ActionViewHelper._computeStickersDiff(orig=sourceState, new=state)
            ActionViewHelper._markMapDiff(sourceState, state)

            scheduled = [ActionViewHelper._dbScheduleAction(scheduledAction, source=dbAction, author=request.user)
                         for scheduledAction in commitResult.scheduledActions]

            awardedStickers = ActionViewHelper._awardStickers(gainedStickers)
            ActionViewHelper.addResultNotifications(commitResult)

            return Response(data={
                "success": True,
                "expected": commitResult.expected,
                "message": ActionViewHelper._commitMessage(commitResult, scheduled),
                "stickers": DbStickerSerializer(awardedStickers, many=True).data,
            })
        except ActionFailed as e:
            return ActionViewHelper._actionFailedResponse(e)
        except Exception as e:
            tb = traceback.format_exc()
            return ActionViewHelper._unexpectedErrorResponse(e, tb)

    @action(methods=["POST"], detail=True)
    @transaction.atomic()
    def revert(self, request: Request, pk=True) -> Response:
        dbAction = get_object_or_404(DbAction, pk=pk)
        _, entities = DbEntities.objects.get_revision(dbAction.entitiesRevision)

        dbState = DbState.objects.latest()
        state = dbState.toIr()

        dbInteraction = dbAction.lastInteraction()
        checkInitiatePhase(dbInteraction.phase)

        action = dbInteraction.getActionIr(entities, state)
        if not isinstance(action, TeamInteractionActionBase):
            raise UnexpectedActionTypeError(action, TeamInteractionActionBase)

        try:
            result = action.revertInitiate()
            ActionViewHelper.dbStoreInteraction(dbAction, dbState, InteractionType.revert,
                request.user, state, action)
            return Response({
                "success": True,
                "message": f"## Akce zrušena\n\n{result}"
            })
        except ActionFailed as e:
            return ActionViewHelper._actionFailedResponse(e)
        except Exception as e:
            tb = traceback.format_exc()
            return ActionViewHelper._unexpectedErrorResponse(e, tb)


    @action(methods=["GET"], detail=False)
    @transaction.atomic()
    def unfinished(self, request: Request) -> Response:
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
