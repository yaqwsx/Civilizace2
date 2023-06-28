from collections import defaultdict
from itertools import zip_longest
from typing import Any, Optional, Type

from django.db import transaction
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.exceptions import APIException
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.models.announcement import Announcement, AnnouncementType
from core.models.team import Team
from core.models.user import User
from game.actions import GAME_ACTIONS
from game.actions.actionBase import (
    ActionCommonBase,
    ActionResult,
    NoInitActionBase,
    ScheduledAction,
    TAction,
)
from game.actions.common import ActionFailed, MessageBuilder
from game.entities import Entities, Entity, TeamEntity, Tech
from game.gameGlue import stateDeserialize, stateSerialize
from game.models import (
    DbAction,
    DbEntities,
    DbInteraction,
    DbMapDiff,
    DbScheduledAction,
    DbState,
    DbSticker,
    DbTurn,
    DiffType,
    GameTime,
    InteractionType,
    StickerType,
)
from game.serializers import DbActionSerializer
from game.state import GameState
from game.viewsets.permissions import IsOrg
from game.viewsets.stickers import Sticker


class UnexpectedStateError(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_code = "conflict"

    def __init__(self, detail: str):
        super().__init__(detail=f"Nečekaný stav: {detail}")


class UnexpectedActionTypeError(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_code = "conflict"

    def __init__(self, actual: ActionCommonBase, expected: Type[ActionCommonBase]):
        assert not isinstance(actual, expected)
        super().__init__(
            detail=f"Nečekaný typ akce: {type(actual).__name__} (očekávalo se {expected.__name__})"
        )


class ActionViewHelper:
    @staticmethod
    def constructAction(
        actionType: str, args: dict[str, Any], entities: Entities, state: GameState
    ) -> ActionCommonBase:
        Action = GAME_ACTIONS[actionType]
        try:
            argsObj = stateDeserialize(Action.argument, args, entities)
        except KeyError as e:
            raise UnexpectedStateError(f"Invalid args to action (KeyError: {e})") from e
        return Action.action.makeAction(state=state, entities=entities, args=argsObj)

    @staticmethod
    def constructActionFromType(
        actionType: Type[TAction],
        args: dict[str, Any],
        entities: Entities,
        state: GameState,
    ) -> TAction:
        action = ActionViewHelper.constructAction(
            actionType.__name__, args, entities, state
        )
        assert isinstance(action, actionType)
        return action

    @staticmethod
    def dbStoreInteraction(
        db_action: DbAction,
        source_db_state: DbState,
        interaction_type: InteractionType,
        user: Optional[User],
        new_state: GameState,
        action: ActionCommonBase,
    ):
        new_dbstate = DbState.objects.create_from(new_state, source=source_db_state)
        interaction = DbInteraction.objects.create(
            phase=interaction_type,
            action=db_action,
            author=user,
            actionObject=stateSerialize(action),
            trace=action._trace.message,
            new_state=new_dbstate,
        )

        if newDescription := action.description:
            db_action.description = newDescription
            db_action.save()

    @staticmethod
    def addResultNotifications(result: ActionResult) -> None:
        now = timezone.now()
        for t, messages in result.notifications.items():
            team = Team.objects.get(pk=t.id)
            for message in messages:
                a = Announcement.objects.create(
                    author=None,
                    appearDatetime=now,
                    type=AnnouncementType.game,
                    content=message,
                )
                a.teams.add(team)

    @staticmethod
    def _computeStickersDiff(*, orig: GameState, new: GameState) -> set[Sticker]:
        stickers: defaultdict[TeamEntity, set[Entity]] = defaultdict(set)
        for team, newTeamState in new.teamStates.items():
            stickers[team].update(newTeamState.collectStickerEntitySet())
        for team, origTeamState in orig.teamStates.items():
            stickers[team].difference_update(origTeamState.collectStickerEntitySet())
        result = set()
        for team, teamStickers in stickers.items():
            for entity in teamStickers:
                result.add(Sticker(team, entity))
        return result

    @staticmethod
    def _markMapDiff(prev: GameState, post: GameState) -> None:
        """
        Given two states, builds a DbDiff instances that describe the change.
        """
        for k in prev.map.tiles.keys():
            old = prev.map.tiles[k]
            new = post.map.tiles[k]
            if old.richnessTokens != new.richnessTokens:
                DbMapDiff.objects.create(
                    type=DiffType.richness,
                    tile=old.entity.id,
                    newRichness=new.richnessTokens,
                )

        return  # TODO: redo map diff (broken by moving armies)
        for old, new in zip_longest(prev.map.armies, post.map.armies):
            if old is None:
                DbMapDiff.objects.create(
                    type=DiffType.armyCreate,
                    tile=new.tile.id if new.tile is not None else None,
                    newLevel=new.level,
                    armyName=new.name,
                    team=new.team.id,
                )
                return
            if old.level != new.level:
                DbMapDiff.objects.create(
                    type=DiffType.armyLevel,
                    newLevel=new.level,
                    armyName=new.name,
                    team=new.team.id,
                )
            if old.currentTile != new.currentTile:
                DbMapDiff.objects.create(
                    type=DiffType.armyMove,
                    armyName=new.name,
                    team=new.team.id,
                    tile=new.tile.id if new.currentTile is not None else None,
                )

    @staticmethod
    @transaction.atomic
    def _awardStickers(stickers: set[Sticker]) -> list[DbSticker]:
        if len(stickers) == 0:
            return []

        entRevision = DbEntities.objects.latest().id
        awardedStickers: list[DbSticker] = []
        for sticker in stickers:
            dbTeam = Team.objects.get(pk=sticker.team.id)
            if isinstance(sticker.entity, Tech):
                if not DbSticker.objects.filter(entityId=sticker.entity.id).exists():
                    stickerType = StickerType.techFirst
                else:
                    stickerType = StickerType.techSmall
            else:
                stickerType = StickerType.regular

            dbSticker = DbSticker.objects.create(
                team=dbTeam,
                entityId=sticker.entity.id,
                entityRevision=entRevision,
                type=stickerType,
            )
            awardedStickers.append(dbSticker)
        return awardedStickers

    @staticmethod
    def _dbScheduleAction(
        scheduled: ScheduledAction, *, source: DbAction, author: Optional[User]
    ) -> DbScheduledAction:
        gameTime = GameTime.getNearestTime()

        dbAction = DbAction.objects.create(
            actionType=scheduled.actionName,
            entitiesRevision=source.entitiesRevision,
            args=stateSerialize(scheduled.args),
        )
        return DbScheduledAction.objects.create(
            action=dbAction,
            delay_s=scheduled.delay_s,
            author=author,
            created_from=source,
            start_round=gameTime.round,
            start_time_s=gameTime.time,
        )

    @staticmethod
    @transaction.atomic
    def performScheduledAction(scheduled: DbScheduledAction) -> None:
        if scheduled.performed:
            return

        dbAction = scheduled.action
        _, entities = DbEntities.objects.get_revision(dbAction.entitiesRevision)

        dbState = DbState.get_latest()
        state = dbState.toIr()
        sourceState = dbState.toIr()

        action = ActionViewHelper.constructAction(
            dbAction.actionType, dbAction.args, entities, state
        )
        if not isinstance(action, NoInitActionBase):
            raise UnexpectedActionTypeError(action, NoInitActionBase)
        result = action.commit()
        ActionViewHelper.dbStoreInteraction(
            dbAction, dbState, InteractionType.commit, None, action.state, action
        )

        scheduled.performed = True
        scheduled.save()

        ActionViewHelper.addResultNotifications(result)
        ActionViewHelper._markMapDiff(sourceState, state)

    @staticmethod
    def _previewScheduledAction(
        scheduled: ScheduledAction,
        team: Optional[TeamEntity],
        entities: Entities,
        state: GameState,
    ) -> str:
        if scheduled.delay_s != 0:
            delayMsg = f"za {round(scheduled.delay_s / 60)} minut"
        else:
            delayMsg = "ihned"
        b = MessageBuilder(f"**Akce má odložený efekt, který se provede {delayMsg}**:")

        try:
            action = scheduled.actionType.makeAction(
                state=state, entities=entities, args=scheduled.args
            )
            scheduledResult = action.commit()

            b += MessageBuilder(
                f"### Odložený Efekt ({'' if scheduledResult.expected else 'NE'}úspěch)",
                scheduledResult.message,
            )

            for team in [team] if team is not None else scheduledResult.notifications:
                if len(scheduledResult.notifications.get(team, [])) == 0:
                    continue
                b += f"### Notifikace pro tým [[{team.id}]]:"
                for notification in scheduledResult.notifications[team]:
                    b += notification

            with b.startList(
                "### Odložená akce má další odložené efekty:"
            ) as previewScheduledEffect:
                for scheduled in scheduledResult.scheduledActions:
                    previewScheduledEffect(
                        f"za {round(scheduled.delay_s / 60)} minut**"
                    )
        except ActionFailed as e:
            b += "**Odložená akce by v tuto chvíli neuspěla**"
            b += f"{e}"
        except Exception as e:
            b += "**Odložená akce by v tuto chvíli neuspěla (neznámá chyba - řekni to Maarovi)**"

        return b.message

    @staticmethod
    def _commitMessage(
        commitResult: ActionResult,
        scheduled: list[DbScheduledAction],
    ) -> str:
        b = MessageBuilder("## Efekty", commitResult.message)

        assert len(scheduled) == len(commitResult.scheduledActions)
        for action in scheduled:
            targetGameTime = action.targetGameTime()
            if targetGameTime is not None:
                gameTimeStr = f"v {targetGameTime}"
            else:
                gameTimeStr = f"po konci nastavené hry"
            b += f"**Akce má odložený efekt za {round(action.delay_s / 60)} min ({gameTimeStr}).**"

        return b.message

    @staticmethod
    def _actionFailedResponse(e: ActionFailed) -> Response:
        return Response(
            data={
                "success": False,
                "message": MessageBuilder("Akci nelze zadat:", str(e)).message,
            }
        )

    @staticmethod
    def _unexpectedErrorResponse(e: Exception, traceback: str) -> Response:
        return Response(
            data={
                "success": False,
                "message": MessageBuilder(
                    f"Nastala chyba, kterou je třeba zahlásit Maarovi:",
                    str(e),
                    f"```\n{traceback}```",
                ).message,
            }
        )

    @staticmethod
    def _ensureGameIsRunning(actionName: str) -> None:
        try:
            DbTurn.getActiveTurn()
        except DbTurn.DoesNotExist:
            raise ActionFailed("Hra neběží. Není možné zadávat akce.") from None


class ActionResultsSetPagination(PageNumberPagination):
    page_size = 100
    page_size_query_param = "page_size"
    max_page_size = 1000


class ActionLogViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (IsAuthenticated, IsOrg)
    pagination_class = ActionResultsSetPagination
    queryset = DbAction.objects.all().order_by("-id").prefetch_related("interactions")
    serializer_class = DbActionSerializer
