from django.db import models
from django_enumfield import enum

from game.data import TechModel, ResourceModel, ResourceTypeModel
from game.data.entity import AchievementModel
from game.parameters import INITIAL_POPULATION
from .fields import JSONField, ListField
from .immutable import ImmutableModel

import game.managers
import json

from .translations import Translations

from game.managers import PrefetchManager
from game.models.actionBase import ActionStep, InvalidActionException
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
        if isinstance(teamId, Team):
            teamId = teamId.id
        for ts in self.teamStates.all():
            if ts.team.id == teamId:
                return ts
        return None

    def __str__(self):
        return json.dumps(self._dict)


class WorldState(ImmutableModel):
    class WorldStateManager(models.Manager):
        def createInitial(self):
            generation = 0
            return self.create(generation=generation)

    objects = WorldStateManager()

    data = JSONField()
    generation = models.IntegerField()

    def __str__(self):
        return json.dumps(self._dict)


class TeamState(ImmutableModel):
    class TeamStateManager(models.Manager):
        def createInitial(self, team):
            sandbox = SandboxTeamState.objects.createInitial()
            population = PopulationTeamState.objects.createInitial()
            resources = ResourceStorage.objects.createInitial(team)
            techs = TechStorage.objects.createInitial(team)
            distances = DistanceLogger.objects.createInitial(team)
            achievements = TeamAchievements.objects.createInitial()
            return self.create(team=team, sandbox=sandbox, population=population, turn=0, resources=resources,
                               techs=techs, distances=distances, achievements=achievements)

    objects = TeamStateManager()

    team = models.ForeignKey("Team", on_delete=models.PROTECT)
    population = models.ForeignKey("PopulationTeamState", on_delete=models.PROTECT)
    sandbox = models.ForeignKey("SandboxTeamState", on_delete=models.PROTECT)
    turn = models.IntegerField()
    resources = models.ForeignKey("ResourceStorage", on_delete=models.PROTECT)
    techs = models.ForeignKey("TechStorage", on_delete=models.PROTECT)
    distances = models.ForeignKey("DistanceLogger", on_delete=models.PROTECT)
    achievements = models.ForeignKey("TeamAchievements", on_delete=models.PROTECT)

    def __str__(self):
        return json.dumps(self._dict)

    def nextTurn(self):
        self.turn += 1

class TeamAchievements(ImmutableModel):
    class TeamAchievementsManager(models.Manager):
        def createInitial(self):
            return self.create(list=[])

    list = ListField(model_type=AchievementModel)
    objects = TeamAchievementsManager()

    def awardNewAchievements(self, state, team):
        """ Checks if new achievements should be awarded, if so, return their list """
        newAchievements = []
        for achievement in AchievementModel.objects.all():
            if self.list.has(id=achievement.id): # Skip already awarded achievements
                continue
            if achievement.achieved(state, team):
                newAchievements.append(achievement)
                self.list.append(achievement)
        return newAchievements

class DistanceItemProductions(ImmutableModel):
    source = models.ForeignKey("ResourceModel", on_delete=models.PROTECT, related_name="distance_source")
    target = models.ForeignKey("ResourceModel", on_delete=models.PROTECT, related_name="distance_target")
    distance = models.IntegerField()

    def __str__(self):
        return f"{self.source}<->{self.target}={self.distance}"

class DistanceItemTeams(ImmutableModel):
    team = models.ForeignKey("Team", on_delete=models.PROTECT)
    distance = models.IntegerField()

class DistanceLogger(ImmutableModel):
    class DistanceLoggerManager(models.Manager):
        def createInitial(self, team):
            result = self.create(productions=[], teams=[])
            return result
    objects = DistanceLoggerManager()

    productions = ListField(model_type=DistanceItemProductions)
    teams = ListField(model_type=DistanceItemTeams)

    def hasProductionDistance(self, source, target):
        try:
            self.getProductionDistance(source, target)
            return True
        except ValueError:
            return False

    def getProductionDistance(self, source, target):
        if isinstance(source, str):
            source = ResourceModel.objects.get(id=source)
        if isinstance(target, str):
            target = ResourceModel.objects.get(id=target)
        items = list(filter(
            lambda item:
                       (item.source == source and item.target == target)
                       or (item.source == target and item.target == source),
            self.productions
        ))
        assert len(items) <= 1, f"There are multiple distance records for {source} <-> {target}"
        if not len(items):
            raise ValueError(f"No distance mapping between {source} <-> {target}")
        return items[0].distance

    def setProductionDistance(self, source, target, distance):
        if isinstance(source, str):
            source = ResourceModel.objects.get(id=source)
        if isinstance(target, str):
            target = ResourceModel.objects.get(id=target)
        items = list(filter(
            lambda item:
                       (item.source == source and item.target == target)
                       or (item.source == target and item.target == source),
            self.productions
        ))
        item = None
        assert len(items) <= 1, f"There are multiple distance records for {source} -> {target}"
        if not len(items):
            item = DistanceItemProductions(source=source, target=target, distance=distance)
            self.productions.append(item)
        else:
            item = items[0]
        item.distance = distance

    def __str__(self):
        return f"Distances: {self.productions}; {self.teams}"

class ResourceStorageItem(ImmutableModel):
    resource = models.ForeignKey("ResourceModel", on_delete=models.PROTECT)
    amount = models.IntegerField()


class ResourceStorage(ImmutableModel):
    class NotEnoughResourcesException(InvalidActionException):
        pass

    class ResourceStorageManager(models.Manager):
        def createInitial(self, team):
            initialResources = [("res-obyvatel", INITIAL_POPULATION), ("res-prace", INITIAL_POPULATION)]

            if team.id == 1: # TODO: remove DEBUG initial entities
                initialResources.extend([("prod-bobule",20), ("prod-drevo",20), ("prod-cukr",20)])

            items = []
            for id, amount in initialResources:
                items.append(ResourceStorageItem.objects.create(
                    resource=game.data.ResourceModel.objects.get(id=id),
                    amount=amount
                ))
            result = self.create(items=items)
            return result

    objects = ResourceStorageManager()

    @staticmethod
    def asHtml(resources, separator=", "):
        return separator.join([
            str(value) + "x " + key.id
            for key, value in resources.items()])


    items = ListField(model_type=ResourceStorageItem)

    def __str__(self):
        list = [x.resource.label + ":" + str(x.amount) for x in self.items]
        result = ", ".join(list)
        return result

    def spendWork(self, amount):
        self.payResources({ResourceModel.objects.get(id="res-prace"): amount})

    def getAmount(self, resource):
        if isinstance(resource, str):
            resource = ResourceModel.objects.get(id=resource)
        try:
            item = self.items.get(resource=resource)
            return item.amount
        except ResourceStorageItem.DoesNotExist:
            return 0

    def setAmount(self, resource, amount):
        if isinstance(resource, str):
            resource = ResourceModel.objects.get(id=resource)

        item = None
        try:
            item = self.items.get(resource=resource)
        except ResourceStorageItem.DoesNotExist:
            item = ResourceStorageItem(resource=resource, amount=amount)
            self.items.append(item)

        item.amount = amount

    def hasResources(self, resources):
        for resource, amount in resources.items():
            if resource.id[:4] == "mat-":
                continue
            if self.getAmount(resource) < amount:
                return False
        return True

    def payResources(self, resources):
        """Subtract resources from storage.

        Returns a dict of resources not tracked by storage"""
        if not self.hasResources(resources):
            raise ResourceStorage.NotEnoughResourcesException("Insufficient resources")
        result = {}
        for resource, amount in resources.items():
            if resource.id[:4] == "mat-":
                result[resource] = amount
            else:
                self.setAmount(resource, self.getAmount(resource) - amount)
        return result

    def receiveResources(self, resources):
        """Add resources to storage.

        Returns a dict of resources not tracked by storage"""
        result = {}
        for resource, amount in resources.items():
            if resource.id[:4] == "mat-":
                result[resource] = amount
            else:
                targetAmount = self.getAmount(resource) + amount
                self.setAmount(resource, targetAmount)
        return result

    def getResourcesByType(self, metaResource=None):
        if not metaResource:
            metaResource = ResourceModel.objects.get(id="prod-jidlo-2")
        resourceType = metaResource.type
        level = metaResource.level
        isProduction = metaResource.isProduction


        results = {}
        for item in self.items:
            resource = item.resource
            if resource.type == resourceType and resource.level >= level and resource.isProduction == isProduction:
                results[resource] = item.amount
        return results


class TechStatusEnum(enum.Enum):
    UNKNOWN = 0 # used only for status check; Never stored in DB
    RESEARCHING = 2
    OWNED = 3

    __labels__ = {
        UNKNOWN: "Neznámý",
        RESEARCHING: "Zkoumá se",
        OWNED: "Vyzkoumaný"
    }


class TechStorageItem(ImmutableModel):
    tech = models.ForeignKey("TechModel", on_delete=models.PROTECT)
    status = enum.EnumField(TechStatusEnum)
    def __str__(self):
        return self.tech.label + (":❌" if self.status == TechStatusEnum.RESEARCHING else ":✅")


class TechStorage(ImmutableModel):
    class TechStorageManager(models.Manager):
        def createInitial(self, team):
            initialTechs = ["tech-base"]
            # TODO: Remove DEBUG initialization entities
            if team.id == 1:
                initialTechs.extend(["tech-les", "build-centrum", "build-pila", "tech-lovci", "build-lovci"])
            items = []
            for id in initialTechs:
                items.append(TechStorageItem.objects.create(
                    tech=game.data.TechModel.objects.get(id=id),
                    status=TechStatusEnum.OWNED
                ))
            result = self.create(items=items)
            return result

    objects = TechStorageManager()
    items = ListField(model_type=TechStorageItem)

    def __str__(self):
        list = [x.tech.label + ": " + str(x.status) for x in self.items]
        result = ", ".join(list)
        return result

    def getStatus(self, tech):
        try:
            result = self.items.get(tech=tech).status
            return result if result else TechStatusEnum.UNKNOWN
        except TechStorageItem.DoesNotExist:
            return TechStatusEnum.UNKNOWN

    def setStatus(self, tech, status, enforce=False):
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

        self.items.append(TechStorageItem(tech=tech, status=status))
        return self.items[-1]

    def getOwnedTechs(self):
        result = map(lambda item: item.tech, filter(lambda tech: tech.status == TechStatusEnum.OWNED, self.items))
        return list(result)

    def getTechsUnderResearch(self):
        result = map(lambda item: item.tech, filter(lambda tech: tech.status == TechStatusEnum.RESEARCHING, self.items))
        return list(result)

    def getActionableEdges(self):
        ownedTechs = self.getOwnedTechs()
        startedTechs = list(map(
            lambda item: item.tech,
            filter(
                lambda tech: tech.status == TechStatusEnum.RESEARCHING or tech.status == TechStatusEnum.OWNED,
                self.items)))

        edges = set()
        for item in self.items:
            for edge in item.tech.unlocks_tech.all():
                if edge.dst in startedTechs:
                    continue
                if edge.src not in ownedTechs:
                    continue
                edges.add(edge)

        return list(edges)

    def getVyrobas(self):
        results = []

        for tech in self.getOwnedTechs():
            results.extend(tech.unlock_vyrobas.all())

        return results

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
