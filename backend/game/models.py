from __future__ import annotations

import string
from functools import cached_property
from typing import Dict, Optional, Tuple

from core.models import Team, User
from core.models.fields import JSONField
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import QuerySet
from django.utils import timezone
from django.utils.crypto import get_random_string
from django_enumfield import enum

from game.actions import GAME_ACTIONS
from game.actions.actionBase import ActionArgs, ActionInterface
from game.entities import Entities, Entity
from game.entityParser import parseEntities
from game.gameGlue import stateDeserialize, stateSerialize
from game.state import GameState, MapState, TeamState, WorldState


class DbEntitiesManager(models.Manager):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cache: Dict[int, Entities] = {}

    def get_queryset(self) -> QuerySet[DbEntities]:
        return super().get_queryset().defer("data")

    def get_revision(self, revision: Optional[int] = None) -> Tuple[int, Entities]:
        if revision is None:
            revision = self.latest("id").id
        if revision in self.cache:
            return revision, self.cache[revision]
        dbEntities = self.get(id=revision)

        def reportError(msg: str):
            raise RuntimeError(msg)
        entities = parseEntities(
            dbEntities.data, reportError=reportError).gameOnlyEntities
        self.cache[revision] = entities
        return revision, entities


class DbEntities(models.Model):
    """
    Represents entity version. Basically stores only raw data and the manager
    provides a method get_revision to get a particular revision in the form of
    Entities type. (cached)
    """
    class Meta:
        get_latest_by = "id"
    data = JSONField("data")
    objects = DbEntitiesManager()


class DbAction(models.Model):
    """
    Represent an action that was input into the system. It stores which action
    it is and what arguments does it use. The action itself is stored in the
    DbInteractionModel.
    """
    actionType = models.CharField("actionType", max_length=64, null=False)
    entitiesRevision = models.IntegerField()
    description = models.TextField(null=True)
    args = JSONField()

    @property
    def lastInteraction(self):
        return DbInteraction.objects.filter(action=self).latest("phase")

    def getArgumentsIr(self, entities) -> ActionArgs:
        ActionTypeInfo = GAME_ACTIONS[self.actionType]
        return stateDeserialize(ActionTypeInfo.argument, self.args, entities)


class InteractionType(enum.Enum):
    initiate = 0
    commit = 1
    cancel = 2
    delayed = 3
    delayedReward = 4


class DbInteraction(models.Model):
    created = models.DateTimeField(
        "Time of creating the action", auto_now_add=True)
    phase = enum.EnumField(InteractionType)
    action = models.ForeignKey(
        DbAction, on_delete=models.CASCADE, null=False, related_name="interactions")
    author = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    workConsumed = models.IntegerField(default=0)
    actionObject = JSONField()

    def getActionIr(self, entities, state) -> ActionInterface:
        ActionTypeInfo = GAME_ACTIONS[self.action.actionType]
        action = stateDeserialize(
            ActionTypeInfo.action, self.actionObject, entities)
        action._generalArgs = self.action.getArgumentsIr(entities)
        action._state = state
        action._entities = entities
        return action


class DbTeamState(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    data = JSONField("data")

    def toIr(self, entities) -> TeamState:
        return stateDeserialize(TeamState, self.data, entities)


class DbMapState(models.Model):
    data = JSONField("data")

    def toIr(self, entities) -> TeamState:
        return stateDeserialize(MapState, self.data, entities)


class DbWorldState(models.Model):
    data = JSONField("data")

    def toIr(self, entities) -> TeamState:
        return stateDeserialize(WorldState, self.data, entities)


class DbStateManager(models.Manager):
    def createFromIr(self, ir: GameState) -> DbState:
        mapState = DbMapState.objects.create(data=stateSerialize(ir.map))
        worldState = DbWorldState.objects.create(data=stateSerialize(ir.world))
        state = self.create(worldState=worldState,
                            mapState=mapState, interaction=None)
        for t, ts in ir.teamStates.items():
            dbTs = DbTeamState.objects.create(
                team=Team.objects.get(id=t.id),
                data=stateSerialize(ts))
            state.teamStates.add(dbTs)
        state.save()
        return state


class DbState(models.Model):
    class Meta:
        get_latest_by = "id"
    mapState = models.ForeignKey(
        DbMapState, on_delete=models.CASCADE, null=False)
    worldState = models.ForeignKey(
        DbWorldState, on_delete=models.CASCADE, null=False)
    teamStates = models.ManyToManyField(DbTeamState)
    interaction = models.ForeignKey(
        DbInteraction, on_delete=models.CASCADE, null=True)

    objects = DbStateManager()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._teamStates = []

    def toIr(self) -> GameState:
        entities = self.entities
        teams = {}
        for ts in self.teamStates.all():
            teams[entities[ts.team.id]] = ts.toIr(entities)
        return GameState(
            teamStates=teams,
            map=self.mapState.toIr(entities),
            world=self.worldState.toIr(entities))

    def updateFromIr(self, ir: GameState) -> None:
        ir.normalize()
        self._teamStates = []
        dirty = False
        sMap = stateSerialize(ir.map)
        if sMap != self.mapState.data:
            dirty = True
            self.mapState.pk = None
            self.mapState.data = sMap
        sWorld = stateSerialize(ir.world)
        if sWorld != self.worldState.data:
            dirty = True
            self.worldState.pk = None
            self.worldState.data = sWorld
        teamMapping = {t.id: t for t in ir.teamStates.keys()}
        for ts in self.teamStates.all():
            sTs = stateSerialize(ir.teamStates[teamMapping[ts.team.id]])
            self._teamStates.append(ts)
            if sTs != ts.data:
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
    def entities(self):
        if self.interaction is None:
            return DbEntities.objects.get_revision()[1]
        return DbEntities.objects.get_revision(self.interaction.action.entitiesRevision)[1]


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
    def occupiedCount(self):
        return self.assignments.filter(finishedAt=None).count()


class DbTaskAssignment(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    task = models.ForeignKey(
        DbTask, on_delete=models.CASCADE, related_name="assignments")
    techId = models.CharField(max_length=32)
    assignedAt = models.DateTimeField(auto_now_add=True)
    finishedAt = models.DateTimeField(null=True)
    abandoned = models.BooleanField(default=False)


class DbTaskPreference(models.Model):
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['task', 'techId'], name='unique_preference')
        ]
    task = models.ForeignKey(
        DbTask, on_delete=models.CASCADE, related_name="techs")
    techId = models.CharField(max_length=32)


class DbTurnManager(models.Manager):
    def getActiveTurn(self):
        object = self.get_queryset() \
            .filter(enabled=True, startedAt__isnull=False).latest()
        if timezone.now() > object.startedAt + timezone.timedelta(seconds=object.duration):
            raise DbTurn.DoesNotExist()
        return object


class DbTurn(models.Model):
    class Meta:
        get_latest_by = "id"
    startedAt = models.DateTimeField(null=True)
    enabled = models.BooleanField(default=False)
    duration = models.IntegerField(
        default=15*60, validators=[MinValueValidator(0)])  # In seconds

    objects = DbTurnManager()

    @cached_property
    def next(self):
        return DbTurn.objects.get(id=self.id + 1)

    @cached_property
    def prev(self):
        try:
            return DbTurn.objects.get(id=self.id - 1)
        except DbTurn.DoesNotExist:
            return None

    @cached_property
    def shouldStartAt(self):
        if self.startedAt is not None:
            return self.startedAt
        return self.prev.shouldStartAt + timezone.timedelta(seconds=self.prev.duration)


class DbDelayedEffect(models.Model):
    slug = models.SlugField(max_length=8)
    team = models.ForeignKey(
        Team, related_name="vouchers", null=True, on_delete=models.CASCADE)
    round = models.IntegerField()
    target = models.IntegerField()  # In seconds
    action = models.ForeignKey(DbAction, on_delete=models.CASCADE)
    stickers = JSONField(null=True)
    performed = models.BooleanField(default=False)
    withdrawn = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._generateSlug()
        super().save(*args, **kwargs)

    @staticmethod
    def _generateSlug() -> str:
        slug = None
        while slug is None:
            slug = get_random_string(5, string.ascii_uppercase)
            if DbDelayedEffect.objects.filter(slug=slug).exists():
                slug = None
        return slug

    @property
    def description(self):
        return self.action.description


class StickerType(models.IntegerChoices):
    regular = 0
    techSmall = 1
    techFirst = 2


class DbSticker(models.Model):
    team = models.ForeignKey(
        Team, related_name="stickers", on_delete=models.CASCADE)
    entityId = models.CharField(max_length=32)
    entityRevision = models.IntegerField()
    type = models.IntegerField(choices=StickerType.choices)
    awardedAt = models.DateTimeField(auto_now_add=True)

    def update(self) -> None:
        self.entityRevision = DbEntities.objects.latest().id

    @property
    def ident(self) -> str:
        return f"sticker_{self.team.id}_{self.entityId}_{self.entityRevision}_{self.type}"

    @cached_property
    def entity(self) -> Entity:
        return DbEntities.objects.get_revision(self.entityRevision)[self.entityId]

    @property
    def stickerPaperRequired(self):
        return self.entityId.startswith("tec-")


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


class DiffType(models.IntegerChoices):
    richness = 0
    armyLevel = 1
    armyMove = 2
    armyCreate = 3


class DbMapDiff(models.Model):
    createdAt = models.DateTimeField(auto_now_add=True)
    type = models.IntegerField(choices=DiffType.choices)
    tile = models.CharField(max_length=32, null=True)
    newRichness = models.IntegerField(null=True)
    newLevel = models.IntegerField(null=True)
    team = models.CharField(max_length=32, null=True)
    armyName = models.CharField(max_length=32, null=True)
