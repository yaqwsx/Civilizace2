from .common import PrefetchManager
import game.models
from django.db import models

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
        action = game.models.Action.objects.createInitial()
        state = self.create(action=action, worldState=worldState)
        state.teamStates.set(teamStates)
        return state

    def getNewest(self):
        return self.latest("action__created", "pk")


class WorldStateManager(models.Manager):
    def createInitial(self):
        return self.create(data={})


class TeamStateManager(models.Manager):
    def createInitial(self, team):
        wealth = game.models.WealthTeamState.objects.createInitial()
        population = game.models.PopulationTeamState.objects.createInitial()
        return self.create(team=team, wealth=wealth, population=population)


class WealthTeamStateManager(models.Manager):
    def createInitial(self):
        return self.create(data={})


class PopulationTeamStateManager(models.Manager):
    def createInitial(self):
        return self.create(data={})


class ActionManager(models.Manager):
    def createInitial(self):
        return self.create(move=game.models.ActionMove.createInitial)