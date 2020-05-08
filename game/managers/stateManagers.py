from .common import PrefetchManager
import game.models
from django.db import models
from game import parameters

class StateManager(PrefetchManager):
    def __init__(self):
        # ManyToMany Field needs to prefetched in order to make immutable models
        # to work intuitively (otherwise the recursive saving does not work as
        # you can get different handles to models)
        super(StateManager, self).__init__(prefetch_related=("teamStates",), select_related=("action",))

    def createInitial(self):
        teamStates = [game.models.TeamState.objects.createInitial(team=team)
            for team in game.models.Team.objects.all()]
        worldState = game.models.WorldState.objects.createInitial()
        action = game.models.ActionStep.objects.createInitial()
        state = self.create(action=action, worldState=worldState)
        state.teamStates.set(teamStates)
        return state

    def getNewest(self):
        return self.latest("pk")


class WorldStateManager(models.Manager):
    def createInitial(self):
        generation = game.models.GenerationWorldState.objects.createInitial()
        return self.create(generation = generation)


class TeamStateManager(models.Manager):
    def createInitial(self, team):
        sandbox = game.models.SandboxTeamState.objects.createInitial()
        population = game.models.PopulationTeamState.objects.createInitial()
        return self.create(team=team, sandbox=sandbox, population=population)


class SandboxTeamStateManager(models.Manager):
    def createInitial(self):
        return self.create(data={
            "counter": 0
        })

class GenerationWorldStateManager(models.Manager):
    def createInitial(self):
        return self.create(
            generation=0
        )

class PopulationTeamStateManager(models.Manager):
    def createInitial(self):
        return self.create(
            work=parameters.INITIAL_POPULATION,
            population=parameters.INITIAL_POPULATION
        )


class ActionManager(models.Manager):
    def createInitial(self):
        return self.create(move=game.models.ActionMove.createInitial, arguments={})

class ActionStepManager(models.Manager):
    def createInitial(self):
        return self.create(
            author = None,
            phase=game.models.ActionPhase.commit,
            action=game.models.Action.objects.createInitial(),
            workConsumed=0)

