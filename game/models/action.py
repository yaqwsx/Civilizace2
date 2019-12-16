from django.db import models
from .immutable import ImmutableModel
from game.managers import ActionManager
import json
from django_enumfield import enum

class ActionMove(enum.Enum):
    createInitial = 0
    increasePopulation = 1

class Action(ImmutableModel):
    created = models.DateTimeField("Time of creating the action", auto_now=True)
    team = models.ForeignKey("Team", on_delete=models.PROTECT, null=True)
    move = enum.EnumField(ActionMove)

    objects = ActionManager()

    def __str__(self):
        return json.dumps(self._dict)

class KeywordCategory(enum.Enum):
    team = 0
    move = 1

class Keyword(models.Model):
    word = models.CharField("Game Word", max_length=30)
    description = models.CharField(max_length=150)
    category = enum.EnumField(KeywordCategory)
    argument1 = models.IntegerField(null=True)
    argument2 = models.IntegerField(null=True)
