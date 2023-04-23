import traceback
from typing import Iterable

from django.db import transaction
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from game.actions import GAME_ACTIONS
from game.actions.actionBase import ActionResult, NoInitActionBase
from game.actions.common import ActionFailed, MessageBuilder
from game.entities import Entities
from game.gameGlue import stateSerialize
from game.models import DbAction, DbEntities, DbState, InteractionType
from game.state import GameState
from game.viewsets.action_view_helper import (ActionViewHelper,
                                              UnexpectedActionTypeError)
from game.viewsets.permissions import IsOrg, IsSuperOrg
from game.viewsets.stickers import DbStickerSerializer, Sticker


class NoInitActionSerializer(serializers.Serializer):
    action = serializers.ChoiceField(list(id for (id, action) in GAME_ACTIONS.items() if issubclass(action.action, NoInitActionBase)))
    args = serializers.JSONField()

class NoInitActionViewSet(viewsets.ViewSet):
    permission_classes = (IsAuthenticated, IsOrg, IsSuperOrg)

    @staticmethod
    def _previewDryCommitMessage(commitResult: ActionResult, stickers: Iterable[Sticker],
            entities: Entities, state: GameState) -> str:
        b = MessageBuilder()
        b.add("## Efekty")
        b.add(commitResult.message)
        with b.startList("Budou vydány samolepky:") as addLine:
            for t, e in stickers:
                addLine(f"samolepka {e.name} pro tým {t.name}")

        for scheduled in commitResult.scheduledActions:
            b += ActionViewHelper._previewScheduledAction(scheduled, team=None, entities=entities, state=state)

        return b.message

    @action(methods=["POST"], detail=False)
    def dry(self, request: Request) -> Response:
        deserializer = NoInitActionSerializer(data=request.data)
        deserializer.is_valid(raise_exception=True)
        data = deserializer.validated_data

        _, entities = DbEntities.objects.get_revision()
        dbState = DbState.objects.latest()
        state = dbState.toIr()
        sourceState = dbState.toIr()

        msgBuilder = MessageBuilder()

        try:
            ActionViewHelper._ensureGameIsRunning(data["action"])
        except ActionFailed as e:
            msgBuilder += str(e)
            msgBuilder += "Ignoring stopped game for preview."
            pass


        try:
            action = ActionViewHelper.constructAction(data["action"], data["args"], entities, state)
            if not isinstance(action, NoInitActionBase):
                raise UnexpectedActionTypeError(action, NoInitActionBase)

            commitResult = action.commit()

            stickers = ActionViewHelper._computeStickersDiff(orig=sourceState, new=action.state)

            message = NoInitActionViewSet._previewDryCommitMessage(commitResult, stickers, entities=action.entities, state=action.state)

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
    def commit(self, request: Request) -> Response:
        deserializer = NoInitActionSerializer(data=request.data)
        deserializer.is_valid(raise_exception=True)
        data = deserializer.validated_data

        try:
            ActionViewHelper._ensureGameIsRunning(data["action"])

            entityRevision, entities = DbEntities.objects.get_revision()
            dbState = DbState.objects.latest()
            state = dbState.toIr()
            sourceState = dbState.toIr()

            action = ActionViewHelper.constructAction(data["action"], data["args"], entities, state)
            if not isinstance(action, NoInitActionBase):
                raise UnexpectedActionTypeError(action, NoInitActionBase)

            commitResult = action.commit()

            dbAction = DbAction.objects.create(
                    actionType=data["action"],
                    entitiesRevision=entityRevision,
                    args=stateSerialize(action.args))
            ActionViewHelper.dbStoreInteraction(dbAction, dbState,
                InteractionType.commit, request.user, state, action)

            stickers = ActionViewHelper._computeStickersDiff(orig=sourceState, new=action.state)
            ActionViewHelper._markMapDiff(sourceState, state)

            scheduled = [ActionViewHelper._dbScheduleAction(scheduledAction, source=dbAction, author=request.user)
                         for scheduledAction in commitResult.scheduledActions]

            awardedStickers = ActionViewHelper._awardStickers(stickers)
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
