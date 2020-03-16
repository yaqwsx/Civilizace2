from django.db import models
from .immutable import ImmutableModel
from .fields import JSONField
from game.managers import ActionManager
import json
from django_enumfield import enum

class ActionMove(enum.Enum):
    createInitial = 0
    sanboxIncreaseCounter = 1

    __labels__ = {
        createInitial: "Vytvořit nový stav",
        sanboxIncreaseCounter: "Zvýšit counter"
    }

class Action(ImmutableModel):
    created = models.DateTimeField("Time of creating the action", auto_now=True)
    team = models.ForeignKey("Team", on_delete=models.PROTECT, null=True)
    move = enum.EnumField(ActionMove)
    arguments = JSONField()

    objects = ActionManager()

    def resolve(self):
        import game.models.action # Required to load all subclasses
        for actionClass in  Action.__subclasses__():
            if actionClass.CiviMeta.move == self.move:
                return actionClass.objects.get(pk=self.pk)
        return None

    def sane(self):
        return move is not None and team is not None

    def build(data):
        import game.models.action # Required to load all subclasses
        move = data["action"]
        for actionClass in  Action.__subclasses__():
            if actionClass.CiviMeta.move == move:
                return actionClass.build(data=data)
        return None

    def formFor(move):
        import game.models.action # Required to load all subclasses
        for actionClass in  Action.__subclasses__():
            if actionClass.CiviMeta.move == move:
                return actionClass.CiviMeta.form
        return None

    def __str__(self):
        return json.dumps(self._dict)