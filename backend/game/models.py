from __future__ import annotations
from enumfields import EnumField
from typing import Dict, Optional
from django.db import models
from django.db.models import QuerySet
from core.models.fields import JSONField
from core.models import Team, User
from game.entities import Entities
from game.entityParser import parseEntities
from enum import Enum

class DbEntitiesManager(models.Manager):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cache: Dict[int, Entities] = {}

    def get_queryset(self) -> QuerySet[DbEntities]:
        return super().get_queryset().defer("data")

    def get_revision(self, revision: Optional[int]=None) -> Entities:
        if revision is None:
            revision = self.latest("id").id
        if revision in self.cache:
            return self.cache[revision]
        dbEntities = self.get(id=revision)

        def reportError(msg: str):
            raise RuntimeError(msg)
        entities = parseEntities(dbEntities.data, reportError=reportError)
        self.cache[revision] = entities
        return entities

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
    data = JSONField("data")

class InteractionType(Enum):
    initiate = 0
    commit = 1
    abandon = 2
    cancel = 3
    postpone = 4

class DbInteraction(models.Model):
    created = models.DateTimeField("Time of creating the action", auto_now=True)
    phase = EnumField(InteractionType)
    models.ForeignKey(DbAction, on_delete=models.PROTECT, null=False)
    author = models.ForeignKey(User, on_delete=models.PROTECT, null=True)
    workConsumed = models.IntegerField()

class DbTeamState(models.Model):
    team = models.ForeignKey(Team, on_delete=models.PROTECT)
    data = JSONField("data")

class DbWorldState(models.Model):
    data = JSONField("data")

class DbState(models.Model):
    worldState = models.ForeignKey(DbWorldState, on_delete=models.PROTECT, null=False)
    teamStates = models.ManyToManyField(DbTeamState)

