from django.db import models
from .fields import JSONField
from .immutable import ImmutableModel
import game.managers
import json

class State(ImmutableModel):
    action = models.ForeignKey("ActionStep", on_delete=models.PROTECT)
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
    class WorldStateManager(models.Manager):
        def createInitial(self):
            generation = game.models.state.GenerationWorldState.objects.createInitial()
            return self.create(generation=generation)
    objects = WorldStateManager()

    data = JSONField()
    generation = models.ForeignKey("GenerationWorldState", on_delete=models.PROTECT)

    def __str__(self):
        return json.dumps(self._dict)

class GenerationWorldState(ImmutableModel):
    class GenerationWorldStateManager(models.Manager):
        def createInitial(self):
            return self.create(
                generation=0
            )

    generation = models.IntegerField("generation")
    objects = GenerationWorldStateManager()

    def __str__(self):
        return json.dumps(self._dict)

    def nextGeneration(self):
        self.generation += 1


class TeamState(ImmutableModel):
    class TeamStateManager(models.Manager):
        def createInitial(self, team):
            sandbox = game.models.SandboxTeamState.objects.createInitial()
            population = game.models.PopulationTeamState.objects.createInitial()
            return self.create(team=team, sandbox=sandbox, population=population, turn=0)
    objects = TeamStateManager()

    team = models.ForeignKey("Team", on_delete=models.PROTECT)
    population = models.ForeignKey("PopulationTeamState", on_delete=models.PROTECT)
    sandbox = models.ForeignKey("SandboxTeamState", on_delete=models.PROTECT)
    turn = models.IntegerField()


    def __str__(self):
        return json.dumps(self._dict)

    def nextTurn(self):
        self.turn += 1

# =================================================
class PopulationTeamState(ImmutableModel):
    population = models.IntegerField("population")
    work = models.IntegerField("work")

    objects = game.managers.PopulationTeamStateManager()

    def __str__(self):
        return json.dumps(self._dict)

    def startNewRound(self):
        self.work = self.work // 2
        self.work += self.population

class SandboxTeamState(ImmutableModel):
    data = JSONField()

    objects = game.managers.SandboxTeamStateManager()

    def __str__(self):
        return json.dumps(self._dict)

