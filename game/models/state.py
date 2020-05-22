from django.db import models
from django_enumfield import enum

from game.data import TechModel
from .fields import JSONField
from .immutable import ImmutableModel

import game.managers
import json

from .translations import Translations

from game.managers import PrefetchManager
from game.models.actionBase import ActionStep
from game.models.users import Team
from game import parameters


class StateManager(PrefetchManager):
    def __init__(self):
        # ManyToMany Field needs to prefetched in order to make immutable models
        # to work intuitively (otherwise the recursive saving does not work as
        # you can get different handles to models)
        super(StateManager, self).__init__(prefetch_related=("teamStates",), select_related=("action",))

    def createInitial(self):
        teamStates = [TeamState.objects.createInitial(team=team)
                      for team in Team.objects.all()]
        worldState = WorldState.objects.createInitial()
        action = ActionStep.objects.createInitial()
        state = self.create(action=action, worldState=worldState)
        state.teamStates.set(teamStates)
        return state

    def getNewest(self):
        return self.latest("pk")


class State(ImmutableModel):
    action = models.ForeignKey("ActionStep", on_delete=models.PROTECT)
    worldState = models.ForeignKey("WorldState", on_delete=models.PROTECT)
    teamStates = models.ManyToManyField("TeamState")

    objects = StateManager()

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
            sandbox = SandboxTeamState.objects.createInitial()
            population = PopulationTeamState.objects.createInitial()
            resources = ResourceStorage.objects.createInitial()
            techs = TechStorage.objects.createInitial()
            return self.create(team=team, sandbox=sandbox, population=population, turn=0, resources=resources,
                               techs=techs)

    objects = TeamStateManager()

    team = models.ForeignKey("Team", on_delete=models.PROTECT)
    population = models.ForeignKey("PopulationTeamState", on_delete=models.PROTECT)
    sandbox = models.ForeignKey("SandboxTeamState", on_delete=models.PROTECT)
    turn = models.IntegerField()
    resources = models.ForeignKey("ResourceStorage", on_delete=models.PROTECT)
    techs = models.ForeignKey("TechStorage", on_delete=models.PROTECT)

    def __str__(self):
        return json.dumps(self._dict)

    def nextTurn(self):
        self.turn += 1


class ResourceStorageItem(ImmutableModel):
    resource = models.ForeignKey("ResourceModel", on_delete=models.PROTECT)
    amount = models.IntegerField()


class ResourceStorage(ImmutableModel):
    class ResourceStorageManager(models.Manager):
        def createInitial(self):
            initialResources = [("res-obyvatel", 100), ("res-prace", 100)]
            items = []
            for id, amount in initialResources:
                print("id: " + str(id))
                items.append(ResourceStorageItem.objects.create(
                    resource=game.data.ResourceModel.objects.get(id=id),
                    amount=amount
                ))
            result = self.create()
            result.items.set(items)
            return result

    objects = ResourceStorageManager()

    items = models.ManyToManyField("ResourceStorageItem")

    def __str__(self):
        list = [x.resource.label + ":" + str(x.amount) for x in self.items.all()]
        result = ", ".join(list)
        return result


class TechStatusEnum(enum.Enum):
    UNKNOWN = 0
    VISIBLE = 1
    RESEARCHING = 2
    OWNED = 3

    __labels__ = {
        UNKNOWN: "Neznámý",
        VISIBLE: "Viditelný",
        RESEARCHING: "Zkoumá se",
        OWNED: "Vyzkoumaný"
    }


class TechStorageItem(ImmutableModel):
    tech = models.ForeignKey("TechModel", on_delete=models.PROTECT)
    status = enum.EnumField(TechStatusEnum)


class TechStorage(ImmutableModel):
    class TechStorageManager(models.Manager):
        def createInitial(self):
            initialTechs = ["tech-base", "tech-les"]
            items = []
            for id in initialTechs:
                print("id: " + str(id))
                items.append(TechStorageItem.objects.create(
                    tech=game.data.TechModel.objects.get(id=id),
                    status=TechStatusEnum.OWNED
                ))
            result = self.create()
            result.items.set(items)
            return result

    objects = TechStorageManager()
    items = models.ManyToManyField("TechStorageItem")

    def __str__(self):
        list = [x.tech.label + ": " + str(x.status) for x in self.items.all()]
        result = ", ".join(list)
        return result

    def setStatus(self, tech, status):
        previousItem = None
        try:
            previousItem = self.items.get(tech=tech)
        except TechStorageItem.DoesNotExist:
            pass

        if previousItem:
            if status < previousItem.status:
                raise Exception("Cannot downgrade status of " + tech.label)
            if status == previousItem.status:
                return previousItem
            self.items.remove(previousItem)

        newItem = TechStorageItem.objects.create(tech=tech, status=status)
        newItem.save()
        self.items.add(newItem)
        return newItem

    def getOwnedTechs(self):
        result = []
        for item in self.items.all():
            if item.status == TechStatusEnum.OWNED:
                result.append(item.tech)
        return result

    def getVisibleEdges(self):
        owned = self.getOwnedTechs()
        result = []
        for item in self.items.all():
            for edge in item.tech.unlocks_tech.all():
                if edge.dst in owned:
                    pass
                else:
                    result.append(edge)
        return result
        # TODO: Jak v template udelat to, co se deje v commentu?
        # return [edge.label for edge in result]

# =================================================

class PopulationTeamStateManager(models.Manager):
    def createInitial(self):
        return self.create(
            work=parameters.INITIAL_POPULATION,
            population=parameters.INITIAL_POPULATION
        )


class PopulationTeamState(ImmutableModel):
    population = models.IntegerField("population")
    work = models.IntegerField("work")

    objects = PopulationTeamStateManager()

    def __str__(self):
        return json.dumps(self._dict)

    def startNewRound(self):
        self.work = self.work // 2
        self.work += self.population


class SandboxTeamStateManager(models.Manager):
    def createInitial(self):
        return self.create(data={
            "counter": 0
        })


class SandboxTeamState(ImmutableModel):
    data = JSONField()

    objects = SandboxTeamStateManager()

    def __str__(self):
        return json.dumps(self._dict)
