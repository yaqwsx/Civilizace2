from __future__ import annotations
from django.utils.crypto import get_random_string
import decimal
import json
from enumfields import EnumField
from typing import Any, Dict, Optional, Tuple
from django.db import models
from django.db.models import QuerySet
from django.core.validators import MinValueValidator
from django.utils import timezone
from pydantic import BaseModel
from core.models.fields import JSONField
from core.models import Team, User
from game.entities import Entities, Entity, EntityBase
from game.entityParser import parseEntities
from enum import Enum
from game.gameGlue import stateDeserialize, stateSerialize
from functools import cached_property
import string

from game.state import GameState, MapState, TeamState

class DbEntitiesManager(models.Manager):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cache: Dict[int, Entities] = {}

    def get_queryset(self) -> QuerySet[DbEntities]:
        return super().get_queryset().defer("data")

    def get_revision(self, revision: Optional[int]=None) -> Tuple[int, Entities]:
        if revision is None:
            revision = self.latest("id").id
        if revision in self.cache:
            return revision, self.cache[revision]
        dbEntities = self.get(id=revision)

        def reportError(msg: str):
            raise RuntimeError(msg)
        entities = parseEntities(dbEntities.data, reportError=reportError).gameOnlyEntities
        self.cache[revision] = entities
        return revision, entities

class DbEntities(models.Model):
    """
    Represents entity version. Basically stores only raw data and the manager
    provides a method get_revision to get a particular revision in the form of
    Entities type. (cached)
    """
    data = JSONField("data")
    objects = DbEntitiesManager()

class DbAction(models.Model):
    """
    Represent an action that was input into the system. It stores which action
    it is and what arguments does it use.
    """
    actionType = models.CharField("actionType",max_length=64, null=False)
    entitiesRevision = models.IntegerField()
    args = JSONField("data")
    cost = JSONField("cost")

class InteractionType(Enum):
    initiate = 0
    commit = 1
    abandon = 2
    cancel = 3
    delayed = 4
    delayedReward = 5

class DbInteraction(models.Model):
    created = models.DateTimeField("Time of creating the action", auto_now=True)
    phase = EnumField(InteractionType)
    action = models.ForeignKey(DbAction, on_delete=models.PROTECT, null=False, related_name="interactions")
    author = models.ForeignKey(User, on_delete=models.PROTECT, null=True)
    workConsumed = models.IntegerField(default=0)

class DbTeamState(models.Model):
    team = models.ForeignKey(Team, on_delete=models.PROTECT)
    data = JSONField("data")

    def toIr(self, entities) -> TeamState:
        return stateDeserialize(TeamState, self.data, entities)

class DbMapState(models.Model):
    data = JSONField("data")

    def toIr(self, entities) -> TeamState:
        return stateDeserialize(MapState, self.data, entities)

class DbStateManager(models.Manager):
    def createFromIr(self, ir: GameState) -> DbState:
        mapState = DbMapState.objects.create(data=stateSerialize(ir.map))
        state = self.create(turn=ir.turn, mapState=mapState, interaction=None)
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
    turn = models.IntegerField()
    mapState = models.ForeignKey(DbMapState, on_delete=models.PROTECT, null=False)
    teamStates = models.ManyToManyField(DbTeamState)
    interaction = models.ForeignKey(DbInteraction, on_delete=models.PROTECT, null=True)

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
            turn=self.turn,
            teamStates=teams,
            map=self.mapState.toIr(entities))

    def updateFromIr(self, ir: GameState) -> None:
        dirty = False
        if self.turn != ir.turn:
            dirty = True
            self.turn = ir.turn
        sMap = stateSerialize(ir.map)
        if sMap != self.mapState.data:
            dirty = True
            self.mapState.id = None
            self.mapState.data = sMap
        teamMapping = {t.id: t for t in ir.teamStates.keys()}
        for ts in self.teamStates.all():
            sTs = stateSerialize(ir.teamStates[teamMapping[ts.team.id]])
            if sTs != ts.data:
                self.dirty = True
                ts.id = None
                ts.data = sTs
            self._teamStates.append(ts)
        if dirty:
            self.id = None

    def save(self, *args, **kwargs):
        if self.mapState.id is None:
            self.mapState.save()
        for t in self._teamStates:
            if t.id is None:
                t.save()
        super().save(*args, **kwargs)
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
    task = models.ForeignKey(DbTask, on_delete=models.CASCADE, related_name="assignments")
    techId = models.CharField(max_length=32)
    assignedAt = models.DateTimeField(auto_now=True)
    finishedAt = models.DateTimeField(null=True)
    abandoned = models.BooleanField(default=False)

class DbTaskPreference(models.Model):
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['task', 'techId'], name='unique_preference')
        ]
    task = models.ForeignKey(DbTask, on_delete=models.CASCADE, related_name="techs")
    techId = models.CharField(max_length=32)

class DbTurnManager(models.Manager):
    def getActiveTurn(self):
        return self.get_queryset() \
            .filter(enabled=True, startedAt__isnull=False).latest()

class DbTurn(models.Model):
    class Meta:
        get_latest_by = "id"
    startedAt = models.DateTimeField(null=True)
    enabled = models.BooleanField(default=False)
    duration = models.IntegerField(default=1*60, validators=[MinValueValidator(0)]) # In seconds

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
    round = models.IntegerField()
    target = models.IntegerField() # In seconds
    action = models.ForeignKey(DbAction, on_delete=models.PROTECT)
    result = JSONField(null=True)
    stickers = JSONField(null=True)
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
