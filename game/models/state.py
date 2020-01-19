from django.db import models
from .fields import JSONField
from .immutable import ImmutableModel
import game.managers
import json

class State(ImmutableModel):
    action = models.ForeignKey("Action", on_delete=models.PROTECT)
    worldState = models.ForeignKey("WorldState", on_delete=models.PROTECT)
    teamStates = models.ManyToManyField("TeamState")

    objects = game.managers.StateManager()

    def teamState(self, teamId):
        for ts in self.teamStates.all():
            if ts.team.id == teamId:
                return ts
        return None

    def __str__(self):
        return json.dumps(self._dict)

class WorldState(ImmutableModel):
    data = JSONField()

    objects = game.managers.WorldStateManager()

    def __str__(self):
        return json.dumps(self._dict)

class TeamState(ImmutableModel):
    team = models.ForeignKey("Team", on_delete=models.PROTECT)
    population = models.ForeignKey("PopulationTeamState", on_delete=models.PROTECT)
    sandbox = models.ForeignKey("SandboxTeamState", on_delete=models.PROTECT)

    objects = game.managers.TeamStateManager()

    def __str__(self):
        return json.dumps(self._dict)

class SandboxTeamState(ImmutableModel):
    data = JSONField()

    objects = game.managers.SandboxTeamStateManager()

    def __str__(self):
        return json.dumps(self._dict)

class PopulationTeamState(ImmutableModel):
    data = JSONField()

    objects = game.managers.PopulationTeamStateManager()

    def __str__(self):
        return json.dumps(self._dict)
