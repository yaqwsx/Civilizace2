from __future__ import annotations

import functools
import math
from functools import cached_property
from typing import Dict, NamedTuple, Optional, Tuple

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import QuerySet
from django.utils import timezone
from django_enumfield import enum

from core.models import Team, User
from core.models.fields import JSONField
from game.actions import GAME_ACTIONS
from game.actions.actionBase import ActionArgs, ActionCommonBase
from game.entities import Entities, Entity
from game.entityParser import EntityParser, ErrorHandler
from game.gameGlue import stateDeserialize, stateSerialize
from game.state import GameState, MapState, TeamState, WorldState


def print_time(time_s: int) -> str:
    return f"{time_s // 60:02}:{time_s % 60:02}"


@functools.total_ordering
class GameTime(NamedTuple):
    round: DbTurn
    time: int

    @property
    def round_id(self) -> int:
        return self.round.id

    @property
    def secs(self) -> int:
        return self.time % 60

    @property
    def mins(self) -> int:
        return self.time // 60

    def __str__(self) -> str:
        return f"{self.round_id}–{self.mins:02}:{self.secs:02}"

    def __lt__(self, other: GameTime) -> bool:
        if not isinstance(other, GameTime):
            raise TypeError(
                f"comparison not supported between instances of '{type(self).__name__}' and '{type(other).__name__}'"
            )
        return self.round_id < other.round_id or (
            self.round_id == other.round_id and self.time < other.time
        )

    @staticmethod
    def getNearestTime() -> GameTime:
        turn = (
            DbTurn.objects.filter(enabled=True, startedAt__isnull=False)
            .order_by("id")
            .last()
        )
        if turn is None:
            turn = DbTurn.objects.earliest("-enabled", "id")

        if turn.startedAt is None:
            return GameTime(turn, 0)

        time_s = math.floor((timezone.now() - turn.startedAt).total_seconds())
        if time_s < 0:
            raise RuntimeError(f"Turn {turn.id} started in the future")
        time_s = min(time_s, turn.duration)
        return GameTime(turn, time_s)


class DbTurn(models.Model):
    class Meta:
        get_latest_by = "id"

    id = models.AutoField(primary_key=True)
    startedAt = models.DateTimeField(null=True)
    enabled = models.BooleanField(default=False)
    duration = models.IntegerField(
        default=15 * 60, validators=[MinValueValidator(0)]
    )  # In seconds

    @staticmethod
    def getActiveTurn() -> DbTurn:
        turn = DbTurn.objects.filter(enabled=True, startedAt__isnull=False).latest("id")
        assert turn.startedAt is not None
        if timezone.now() > turn.startedAt + timezone.timedelta(seconds=turn.duration):
            # Turn already ended
            raise DbTurn.DoesNotExist()
        return turn

    @cached_property
    def next(self) -> DbTurn:
        return DbTurn.objects.get(id=self.id + 1)

    @cached_property
    def prev(self) -> Optional[DbTurn]:
        try:
            return DbTurn.objects.get(id=self.id - 1)
        except DbTurn.DoesNotExist:
            return None


class DbEntitiesManager(models.Manager):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.cache: Dict[int, Entities] = {}

    def get_queryset(self) -> QuerySet[DbEntities]:
        return super().get_queryset().defer("data")

    def get_revision(self, revision: Optional[int] = None) -> Tuple[int, Entities]:
        if revision is None:
            revision = self.latest("id").id
            assert revision is not None
        if revision in self.cache:
            return revision, self.cache[revision]
        dbEntities = self.get(id=revision)

        def reportError(msg: str):
            raise RuntimeError(msg)

        gameOnlyEntities = EntityParser.parse(
            dbEntities.data,
            err_handler=ErrorHandler(reporter=reportError, no_warn=True),
            result_reporter=lambda x: None,
        ).gameOnlyEntities
        self.cache[revision] = gameOnlyEntities
        return revision, gameOnlyEntities


class DbEntities(models.Model):
    """
    Represents entity version. Basically stores only raw data and the manager
    provides a method get_revision to get a particular revision in the form of
    Entities type. (cached)
    """

    class Meta:
        get_latest_by = "id"

    data = JSONField()
    objects = DbEntitiesManager()


class DbAction(models.Model):
    """
    Represent an action that was input into the system. It stores which action
    it is and what arguments does it use. The action itself is stored in the
    DbInteractionModel.
    """

    id = models.BigAutoField(primary_key=True)
    actionType = models.CharField(max_length=64, null=False)
    entitiesRevision = models.IntegerField()
    description = models.TextField(null=True)
    args = JSONField()

    def lastInteraction(self) -> DbInteraction:
        return DbInteraction.objects.filter(action=self).latest("phase")

    def getArgumentsIr(self, entities: Entities) -> ActionArgs:
        ActionTypeInfo = GAME_ACTIONS[self.actionType]
        return stateDeserialize(ActionTypeInfo.argument, self.args, entities)


class DbScheduledAction(models.Model):
    action = models.ForeignKey(
        DbAction, on_delete=models.CASCADE, null=False, related_name="scheduled"
    )

    created = models.DateTimeField("Time of creating the action", auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_from = models.ForeignKey(
        DbAction, on_delete=models.CASCADE, null=True, related_name="subsequent"
    )

    start_round = models.ForeignKey(DbTurn, on_delete=models.CASCADE)
    start_time_s = models.IntegerField(validators=[MinValueValidator(0)])
    delay_s = models.IntegerField(validators=[MinValueValidator(0)])
    performed = models.BooleanField(default=False)

    @property
    def startGameTime(self) -> GameTime:
        return GameTime(self.start_round, self.start_time_s)

    def targetGameTime(self) -> Optional[GameTime]:
        try:
            turn = self.start_round
            time = self.start_time_s + self.delay_s
            while time >= turn.duration:
                time -= turn.duration
                turn = turn.next
        except DbTurn.DoesNotExist:
            return None
        assert time >= 0
        return GameTime(turn, time)


class InteractionType(enum.Enum):
    initiate = 0
    commit = 1
    revert = 2  # Reverted initiate


class DbInteraction(models.Model):
    created = models.DateTimeField("Time of creating the action", auto_now_add=True)
    phase: InteractionType = enum.EnumField(InteractionType)  # type: ignore
    action = models.ForeignKey(
        DbAction, on_delete=models.CASCADE, null=False, related_name="interactions"
    )
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    actionObject = JSONField()
    trace = models.TextField(default="")

    def getActionIr(self, entities: Entities, state: GameState) -> ActionCommonBase:
        ActionTypeInfo = GAME_ACTIONS[self.action.actionType]
        action = stateDeserialize(ActionTypeInfo.action, self.actionObject, entities)
        action._generalArgs = self.action.getArgumentsIr(entities)
        action._state = state
        action._entities = entities
        return action


class DbTeamState(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    data = JSONField()

    def toIr(self, entities) -> TeamState:
        return stateDeserialize(TeamState, self.data, entities)


class DbMapState(models.Model):
    id = models.BigAutoField(primary_key=True)
    data = JSONField()

    def toIr(self, entities) -> MapState:
        return stateDeserialize(MapState, self.data, entities)


class DbWorldState(models.Model):
    id = models.BigAutoField(primary_key=True)
    data = JSONField()

    def toIr(self, entities) -> WorldState:
        return stateDeserialize(WorldState, self.data, entities)


class DbStateManager(models.Manager):
    def createFromIr(self, ir: GameState) -> DbState:
        mapState = DbMapState.objects.create(data=stateSerialize(ir.map))
        worldState = DbWorldState.objects.create(data=stateSerialize(ir.world))
        state = self.create(worldState=worldState, mapState=mapState, interaction=None)
        for t, ts in ir.teamStates.items():
            dbTs = DbTeamState.objects.create(
                team=Team.objects.get(id=t.id), data=stateSerialize(ts)
            )
            state.teamStates.add(dbTs)
        state.save()
        return state


class DbState(models.Model):
    class Meta:
        get_latest_by = "id"

    mapState = models.ForeignKey(DbMapState, on_delete=models.CASCADE, null=False)
    worldState = models.ForeignKey(DbWorldState, on_delete=models.CASCADE, null=False)
    teamStates = models.ManyToManyField(DbTeamState)
    interaction = models.ForeignKey(DbInteraction, on_delete=models.CASCADE, null=True)

    objects = DbStateManager()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._teamStates = []

    def toIr(self) -> GameState:
        entities = self.entities
        teams = {}
        for ts in self.teamStates.all():
            teams[entities[ts.team.id]] = ts.toIr(entities)
        g = GameState.construct(
            teamStates=teams,
            map=self.mapState.toIr(entities),
            world=self.worldState.toIr(entities),
        )
        g._setParent()
        return g

    def updateFromIr(self, ir: GameState) -> None:
        ir.normalize()
        self._teamStates = []
        dirty = False
        sMap = stateSerialize(ir.map)
        if True or sMap != self.mapState.data:
            dirty = True
            self.mapState.pk = None
            self.mapState.data = sMap
        sWorld = stateSerialize(ir.world)
        if True or sWorld != self.worldState.data:
            dirty = True
            self.worldState.pk = None
            self.worldState.data = sWorld
        teamMapping = {t.id: t for t in ir.teamStates.keys()}
        for ts in self.teamStates.all():
            sTs = stateSerialize(ir.teamStates[teamMapping[ts.team.id]])
            self._teamStates.append(ts)
            if True or sTs != ts.data:
                dirty = True
                ts.pk = None
                ts.data = sTs
        if dirty:
            self.pk = None

    def save(self, *args, **kwargs):
        if self.mapState.id is None:
            mstate = self.mapState
            mstate.save()
            self.mapState = mstate
        if self.worldState.id is None:
            wstate = self.worldState
            wstate.save()
            self.worldState = wstate
        for t in self._teamStates:
            if t.id is None:
                t.save()
        wasDirty = self.pk is None
        super().save(*args, **kwargs)
        if wasDirty:
            self.teamStates.clear()
            for t in self._teamStates:
                self.teamStates.add(t)
            self._teamStates = []

    @property
    def entities(self) -> Entities:
        if self.interaction is None:
            return DbEntities.objects.get_revision()[1]
        return DbEntities.objects.get_revision(
            self.interaction.action.entitiesRevision
        )[1]


class DbTaskManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().prefetch_related("techs")


class DbTask(models.Model):
    id = models.CharField(primary_key=True, max_length=32, null=False)
    name = models.TextField()
    capacity = models.IntegerField()
    orgDescription = models.TextField()
    teamDescription = models.TextField()

    objects = DbTaskManager()

    def save(self, *args, **kwargs):
        if self.id is None or self.id == "":
            self.id = f"ukol-{DbTask.objects.all().count() + 1}"
        super().save(*args, **kwargs)

    @property
    def occupiedCount(self) -> int:
        return self.assignments.filter(finishedAt=None).count()  # type: ignore - related_name from DbTaskAssignment


class DbTaskAssignment(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    task = models.ForeignKey(
        DbTask, on_delete=models.CASCADE, related_name="assignments"
    )
    techId = models.CharField(max_length=32)
    assignedAt = models.DateTimeField(auto_now_add=True)
    finishedAt = models.DateTimeField(null=True)
    abandoned = models.BooleanField(default=False)


class DbTaskPreference(models.Model):
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["task", "techId"], name="unique_preference")
        ]

    task = models.ForeignKey(DbTask, on_delete=models.CASCADE, related_name="techs")
    techId = models.CharField(max_length=32)


class StickerType(enum.Enum):
    regular = 0
    techSmall = 1
    techFirst = 2


class DbSticker(models.Model):
    team = models.ForeignKey(Team, related_name="stickers", on_delete=models.CASCADE)
    entityId = models.CharField(max_length=32)
    entityRevision = models.IntegerField()
    type: StickerType = enum.EnumField(StickerType)  # type: ignore
    awardedAt = models.DateTimeField(auto_now_add=True)

    def update(self) -> None:
        self.entityRevision = DbEntities.objects.latest().id

    @property
    def ident(self) -> str:
        return (
            f"sticker_{self.team.id}_{self.entityId}_{self.entityRevision}_{self.type}"
        )

    @cached_property
    def entity(self) -> Entity:
        return DbEntities.objects.get_revision(self.entityRevision)[1][self.entityId]


class PrinterManager(models.Manager):
    def prune(self):
        """
        Remove dead printers from database. Printer is considered dead after 1
        minute of inactivity.
        """
        criticalPoint = timezone.now() - timezone.timedelta(minutes=1)
        self.filter(registeredAt__lte=criticalPoint).delete()


class Printer(models.Model):
    name = models.CharField(max_length=200)
    address = models.CharField(max_length=200)
    port = models.IntegerField()
    registeredAt = models.DateTimeField(auto_now_add=True)
    printsStickers = models.BooleanField()

    objects = PrinterManager()


class DbTick(models.Model):
    name = models.CharField(max_length=32, primary_key=True)
    lastTick = models.DateTimeField(auto_now=True)


class DiffType(enum.Enum):
    richness = 0
    armyLevel = 1
    armyMove = 2
    armyCreate = 3


class DbMapDiff(models.Model):
    createdAt = models.DateTimeField(auto_now_add=True)
    type: DiffType = enum.EnumField(DiffType)  # type: ignore
    tile = models.CharField(max_length=32, null=True)
    newRichness = models.IntegerField(null=True)
    newLevel = models.IntegerField(null=True)
    team = models.CharField(max_length=32, null=True)
    armyName = models.CharField(max_length=32, null=True)
