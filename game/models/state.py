import math
from django.db import models
from django_enumfield import enum

from game.data import TechModel, ResourceModel, ResourceTypeModel
from game.data.entity import AchievementModel, TaskModel
from game.data.parser import Parser
from game.parameters import INITIAL_POPULATION, MAX_DISTANCE
from .fields import JSONField, ListField
from .immutable import ImmutableModel

import game.managers
import json

from .translations import Translations

from game.managers import PrefetchManager
from game.models.actionBase import ActionStep, InvalidActionException
from game.models.users import Team
from game import parameters

def removeFirstPart(text):
    idx = text.find(".")
    if idx == -1:
        return ""
    return text[idx + 1:]

def eatUpdatePrefix(prefix, updateList):
    """
    Gets and update list (flatten JSON) and selects only keys with given prefix.
    Removes the prefix from the items
    """
    return {
        removeFirstPart(path): value
        for path, value in updateList.items() if path.startswith(prefix)
    }

def eatUpdatePrefixAll(prefix, update):
    return {
        "add": eatUpdatePrefix(prefix, update["add"]),
        "remove": eatUpdatePrefix(prefix, update["remove"]),
        "change": eatUpdatePrefix(prefix, update["change"])
    }

def allowKeys(allowed, list):
    """
    If the list contains not allowed keys, exception is raised
    """
    for key in list.keys():
        if key.split(".")[0] not in allowed:
            raise InvalidActionException(f"Neplatná godMove akce, nedovolený klíč '{key}''")

def extractTeamId(teamDescription):
    startIdx = teamDescription.index("(")
    endIdx = teamDescription.index(")")
    return int(teamDescription[startIdx + 1:endIdx])

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

    def toJson(self):
        json =  {
            "worldState": self.worldState.toJson(),
        }
        json.update({
            f"{ts.team.name}({ts.team.id})" : ts.toJson() for ts in self.teamStates.all()
        })
        return json

    def godUpdate(self, update):
        self.worldState.godUpdate(eatUpdatePrefixAll("worldState", update))
        for ts in self.teamStates.all():
            # ToDo: Ignore the team name
            ts.godUpdate(eatUpdatePrefixAll(f"{ts.team.name}({ts.team.id})", update))

class WorldState(ImmutableModel):
    class WorldStateManager(models.Manager):
        def createInitial(self):
            generation = 0
            foodValue = 20
            castes = "[2,3,4,5]"
            return self.create(
                generation=generation,
                foodValue=foodValue,
                castes=castes,
                storageLimit=10
            )

    objects = WorldStateManager()

    data = JSONField()
    generation = models.IntegerField()
    foodValue = models.IntegerField()
    castes = models.TextField()
    storageLimit = models.IntegerField()

    def __str__(self):
        return json.dumps(self._dict)

    def toJson(self):
        return {
            "generation": self.generation,
            "castes": self.castes,
            "storageLimit": self.storageLimit,
            "foodValue": self.foodValue
        }

    def godUpdate(self, update):
        allowKeys(["generation", "castes", "storageLimit", "foodValue"], update["change"])
        allowKeys([], update["add"])
        allowKeys([], update["remove"])
        if "generation" in update["change"]:
            self.generation = update["change"]["generation"]
        if "castes" in update["change"]:
            self.castes = update["change"]["castes"]
        if "storageLimit" in update["change"]:
            self.storageLimit = update["change"]["storageLimit"]
        if "foodValue" in update["change"]:
            self.foodValue = update["change"]["foodValue"]

    def getCastes(self):
        kasty =  list(json.loads(self.castes))
        kasty.sort(reverse=True)
        return kasty

class TeamState(ImmutableModel):
    class TeamStateManager(models.Manager):
        def createInitial(self, team):
            sandbox = SandboxTeamState.objects.createInitial()
            population = PopulationTeamState.objects.createInitial()
            resources = ResourceStorage.objects.createInitial(team)
            materials = MaterialStorage.objects.createInitial()
            techs = TechStorage.objects.createInitial(team)
            distances = DistanceLogger.objects.createInitial(team)
            achievements = TeamAchievements.objects.createInitial()
            foodSupply = FoodStorage.objects.createInitial()
            vliv = VlivStorage.objects.createInitial()
            return self.create(
                team=team,
                sandbox=sandbox,
                population=population,
                turn=0,
                resources=resources,
                materials=materials,
                techs=techs,
                distances=distances,
                achievements=achievements,
                foodSupply=foodSupply,
                vliv=vliv)

    objects = TeamStateManager()

    team = models.ForeignKey("Team", on_delete=models.PROTECT)
    population = models.ForeignKey("PopulationTeamState", on_delete=models.PROTECT)
    sandbox = models.ForeignKey("SandboxTeamState", on_delete=models.PROTECT)
    turn = models.IntegerField()
    resources = models.ForeignKey("ResourceStorage", on_delete=models.PROTECT)
    materials = models.ForeignKey("MaterialStorage", on_delete=models.PROTECT)
    techs = models.ForeignKey("TechStorage", on_delete=models.PROTECT)
    distances = models.ForeignKey("DistanceLogger", on_delete=models.PROTECT)
    achievements = models.ForeignKey("TeamAchievements", on_delete=models.PROTECT)
    foodSupply = models.ForeignKey("FoodStorage", on_delete=models.PROTECT)
    vliv = models.ForeignKey("VlivStorage", on_delete=models.PROTECT)

    def __str__(self):
        return json.dumps(self._dict)

    def nextTurn(self):
        self.turn += 1

    def toJson(self):
        return {
            "population": self.population.toJson(),
            "sandbox": self.sandbox.toJson(),
            "turn": self.turn,
            "resources": self.resources.toJson(),
            "techs": self.techs.toJson(),
            "distances": self.distances.toJson(),
            "achievements": self.achievements.toJson(),
            "foodSupply": self.foodSupply.toJson(),
            "materials": self.materials.toJson()
        }

    def godUpdate(self, update):
        fields = ["population", "sandbox", "resources", "techs",
                  "distances", "achievements", "foodSupply", "materials"]
        allowKeys(fields + ["turn"], update["change"])
        allowKeys(fields, update["add"])
        allowKeys(fields, update["remove"])
        self.population.godUpdate(eatUpdatePrefixAll("population", update))
        self.sandbox.godUpdate(eatUpdatePrefixAll("sandbox", update))
        self.resources.godUpdate(eatUpdatePrefixAll("resources", update))
        self.techs.godUpdate(eatUpdatePrefixAll("techs", update))
        self.achievements.godUpdate(eatUpdatePrefixAll("achievements", update))
        self.foodSupply.godUpdate(eatUpdatePrefixAll("foodSupply", update))
        self.materials.godUpdate(eatUpdatePrefixAll("materials", update))

        if "turn" in update["change"]:
            self.turn = update["change"]["turn"]

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

    def toJson(self):
        return [ ach.id for ach in self.list ]

    def godUpdate(self, update):
        allowKeys([], update["change"])
        for id in update["add"].get("", []):
            try:
                if self.list.has(id=id):
                    continue
                self.list.append(AchievementModel.objects.get(id=id))
            except AchievementModel.DoesNotExist:
                raise InvalidActionException(f"Unknown id '{id}'")
        for id in update["remove"].get("", []):
            if not self.list.has(id=id):
                raise InvalidActionException(f"Cannot remove '{id}' which is not present in the list")
            self.list.remove(self.list.get(id=id))


class DistanceItemBuilding(ImmutableModel):
    source = models.ForeignKey("TechModel", on_delete=models.PROTECT, related_name="distance_source")
    target = models.ForeignKey("TechModel", on_delete=models.PROTECT, related_name="distance_target")
    distance = models.IntegerField()

    def __str__(self):
        return f"{self.source} -> {self.target}={self.distance}"

class DistanceItemTeams(ImmutableModel):
    team = models.ForeignKey("Team", on_delete=models.PROTECT)
    distance = models.IntegerField()

class MissingDistanceError(RuntimeError):
    def __init__(self, msg, source, target):
        super().__init__(msg)
        self.source = source
        self.target = target

class DistanceLogger(ImmutableModel):
    class DistanceLoggerManager(models.Manager):
        def createInitial(self, team):
            result = self.create(building=[], teams=[])
            return result
    objects = DistanceLoggerManager()

    building = ListField(model_type=DistanceItemBuilding)
    teams = ListField(model_type=DistanceItemTeams)

    def getBuildingDistance(self, source, target):
        if isinstance(source, str):
            source = TechModel.objects.get(id=source)
        if isinstance(target, str):
            target = TechModel.objects.get(id=target)
        if source.id > target.id:
            source, target = target, source
        if source.id == target.id:
            return 0
        try:
            item = self.building.get(source=source.id, target=target.id)
            return item.distance
        except DistanceItemBuilding.DoesNotExist:
            raise MissingDistanceError("No distance specified", source, target)

    def setBuildingDistance(self, source, target, distance):
        if isinstance(source, str):
            source = TechModel.objects.get(id=source)
        if isinstance(target, str):
            target = TechModel.objects.get(id=target)
        if source.id > target.id:
            source, target = target, source
        if source.id == target.id:
            return
        try:
            item = self.building.get(source=source.id, target=target.id)
            if item.distance > distance:
                item.distance = distance
        except DistanceItemBuilding.DoesNotExist:
            self.building.append(DistanceItemBuilding(source=source, target=target, distance=distance))

    def allBuildingDistances(self):
        return {
            (x.source, x.target): x.distance for x in self.building
        }

    def getTeamDistance(self, team):
        try:
            if isinstance(team, str):
                distInfo = self.teams.get(team=team)
            else:
                distInfo = self.teams.get(team=team.id)
            return distInfo.distance
        except DistanceItemTeams.DoesNotExist:
            raise MissingDistanceError("No distance specified", None, team)

    def setTeamDistance(self, team, distance):
        try:
            if isinstance(team, str):
                team = Team.objects.get(id=team)
            distInfo = self.teams.get(team=team.id)
            if distInfo.distance > distance:
                distInfo.distance = distance
        except DistanceItemTeams.DoesNotExist:
            self.teams.append(DistanceItemTeams(team=team, distance=distance))

    def allTeamDistances(self):
        distances = { team: None for team in Team.objects.all() }
        for distInfo in self.teams:
            distances[distInfo.team] = distInfo.distance
        return distances


    def __str__(self):
        return f"Distances: {self.building}; {self.teams}"

    def toJson(self):
        return {
            "building": {
                f"{p.source.id} -> {p.target.id}": p.distance for p in self.building
            },
            "teams": {
                f"{t.team.name}({t.team.id})": t.distance for t in self.teams
            }
        }

    def godUpdate(self, update):
        allowKeys(["building", "teams"], update["change"])
        allowKeys(["building", "teams"], update["add"])
        allowKeys(["building", "teams"], update["remove"])
        self.godUpdatebuilding(eatUpdatePrefixAll("building", update))
        self.godUpdateTeams(eatUpdatePrefixAll("teams", update))

    def godUpdatebuilding(self, update):
        def extractResources(s):
            x = s.split(s, "->")
            return x[0].strip(), x[1].strip()
        for desc, value in update["add"].items():
            source, target = extractResources(desc)
            if self.building.has(source=source, target=target):
                    raise InvalidActionException(f"Cannot add duplicite distance for '{desc}'")
            self.building.append(DistanceItemBuilding(source=source, target=target, distance=value))

        for desc, value in update["remove"].items():
            source, target = extractResources(desc)
            if not self.building.has(source=source, target=target):
                raise InvalidActionException(f"Cannot change '{desc}' which is not present in the list")
            self.building.get(source=source, target=target).distance = value

        for desc, value in update["remove"].items():
            source, target = extractResources(desc)
            if not self.building.has(source=source, target=target):
                raise InvalidActionException(f"Cannot remove '{desc}' which is not present in the list")
            self.building.remove(self.building.get(source=source, target=target))

    def godUpdateTeams(self, update):
        for desc, value in update["add"].items():
            id = extractTeamId(desc)
            if self.teams.has(team=id):
                    raise InvalidActionException(f"Cannot add duplicite distance for team '{id}'")
            self.temas.append(DistanceItemTeams(team=id, distance=value))

        for desc, value in update["remove"].items():
            id = extractTeamId(desc)
            if not self.teams.has(team=id):
                raise InvalidActionException(f"Cannot change '{id}' which is not present in the list")
            self.teams.get(team=id).distance = value

        for desc, value in update["remove"].items():
            id = extractTeamId(desc)
            if not self.teams.has(team=id):
                raise InvalidActionException(f"Cannot remove '{id}' which is not present in the list")
            self.teams.remove(self.teams.get(team=id))


class FoodStorageItem(ImmutableModel):
    resource = models.ForeignKey("ResourceModel", on_delete=models.PROTECT)
    amount = models.IntegerField()

class FoodStorage(ImmutableModel):
    class FoodStorageManager(models.Manager):
        def createInitial(self):
            return self.create(items=[])
    objects = FoodStorageManager()
    items = ListField(model_type=FoodStorageItem)

    def getMissingItems(foodStorage, kasty, population, foodValue):
        populaceKast = []
        kasty.sort(reverse=True)

        floor = math.floor(population/len(kasty))
        extras = population - (floor*len(kasty))

        for lvl in kasty:
            if extras:
                populaceKast.append((lvl, floor+1))
                extras -= 1
            else:
                populaceKast.append( (lvl, floor))

        supplyAmounts = [0,0,0,0,0,0,0]
        luxusAmounts = [0,0,0,0,0,0,0]

        for food, amount in foodStorage.getFoodSupply().items():
            supplyAmounts[food.level] += amount*foodValue
        for luxus, amount in foodStorage.getLuxusSupply().items():
            luxusAmounts[luxus.level] += amount*foodValue


        popSum = 0
        foodSums = [sum(supplyAmounts[n:]) for n in range(7)]
        luxussums = [sum(luxusAmounts[n:]) for n in range(7)]
        result = []

        for kasta in populaceKast:
            popSum += kasta[1]
            foodSupply = foodSums[0]
            qualitySupply = foodSums[kasta[0]]
            luxusSupply = luxusAmounts[kasta[0]]
            foodMissing = popSum - foodSupply
            qualityMissing = popSum - qualitySupply
            luxusMissing = popSum - luxusSupply

            # I know it's ugly. But it works with templates
            result.append((
                Parser.romeLevel(kasta[0]), # Roman letter of the Kasta level
                kasta[0], # kasta level int
                kasta[1], # kasta population
                -foodMissing, # Punfed members of the caste
                math.ceil(max(foodMissing, 0)/foodValue), # food required fto feed this caste
                -qualityMissing, # caste members not fed by appropriate food
                math.ceil(max(qualityMissing, 0)/foodValue), # Quality food required to feed this caste
                -luxusMissing, # unsatisfie caste members
                math.ceil(max(luxusMissing, 0)/foodValue) # luxus required to feed this caste
            ))

        return result

    def getSupply(self, type):
        result = {}

        for item in self.items:
            if item.resource.type == type:
                result[item.resource] = item.amount
        return result

    def getFoodSupply(self):
        return self.getSupply(ResourceTypeModel.objects.get(id="type-jidlo"))

    def getLuxusSupply(self):
        return self.getSupply(ResourceTypeModel.objects.get(id="type-luxus"))

    def addSupply(self, resources):
        item = None
        for resource, amount in resources.items():
            try:
                item = self.items.get(resource=resource)
                item.amount += amount
            except FoodStorageItem.DoesNotExist:
                item = FoodStorageItem(resource=resource, amount=amount)
                self.items.append(item)

    def toJson(self):
        return {
            r.resource.id: r.amount for r in self.items
        }

    def godUpdate(self, update):
        for resource, amount in update["add"].items():
            if self.items.has(resource=resource):
                raise InvalidActionException(f"Cannot add '{resource}' which is already present in the list")
            self.items.append(FoodStorageItem(resource=ResourceModel.objects.get(id=resource), amount=amount))

        for resource, _ in update["remove"].items():
            if not self.items.has(resource=resource):
                raise InvalidActionException(f"Cannot remove '{resource}' which is not present in the list")
            self.items.remove(self.items.get(resource=resource))

        for resource, amount in update["change"].items():
            if not self.items.has(resource=resource):
                raise InvalidActionException(f"Cannot change '{resource}' which is not present in the list")
            self.items.get(resource=resource).amount = amount


class ResourceStorageItem(ImmutableModel):
    resource = models.ForeignKey("ResourceModel", on_delete=models.PROTECT)
    amount = models.IntegerField()

class ResourceStorage(ImmutableModel):
    class NotEnoughResourcesException(InvalidActionException):
        def __init__(self, msg, list):
            super().__init__(msg)
            self.list = list

    class ResourceStorageManager(models.Manager):
        def createInitial(self, team):
            initialResources = [("res-obyvatel", INITIAL_POPULATION), ("res-prace", INITIAL_POPULATION), ("res-populace", INITIAL_POPULATION)]

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
            f'{value}&times; {key.htmlRepr()}'
            for key, value in resources.items()])

    items = ListField(model_type=ResourceStorageItem)

    def __str__(self):
        list = [x.resource.label + ":" + str(x.amount) for x in self.items]
        result = ", ".join(list)
        return result

    def _addPopulation(self, amount):
        self.items.get(resource=ResourceModel.objects.get(id="res-populace")).amount += amount

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

        if item.resource.id == "res-obyvatel":
            diff = amount - item.amount
            if diff > 0:
                self._addPopulation(diff)
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
        missing = {}
        for resource, amount in resources.items():
            if resource.id.startswith("mat-"):
                continue
            owned = self.getAmount(resource)
            if owned < amount:
                missing[resource] = amount - owned
        if len(missing) > 0:
            raise ResourceStorage.NotEnoughResourcesException("Missing resources", missing)
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
        resourceType = metaResource.type if metaResource else None
        level = metaResource.level if metaResource else 2
        isProduction = metaResource.isProduction if metaResource else True

        results = {}
        for item in self.items:
            if item.amount == 0:
                continue
            resource = item.resource
            if ((not resourceType) or resource.type == resourceType)\
                    and resource.level >= level \
                    and resource.isProduction == isProduction:
                results[resource] = item.amount
        return results

    def toJson(self):
        return {
            r.resource.id: r.amount for r in self.items
        }

    def godUpdate(self, update):
        for resource, amount in update["add"].items():
            if self.items.has(resource=resource):
                raise InvalidActionException(f"Cannot add '{resource}' which is already present in the list")
            self.items.append(ResourceStorageItem(resource=ResourceModel.objects.get(id=resource), amount=amount))

        for resource, _ in update["remove"].items():
            if not self.items.has(resource=resource):
                raise InvalidActionException(f"Cannot remove '{resource}' which is not present in the list")
            self.items.remove(self.items.get(resource=resource))

        for resource, amount in update["change"].items():
            if not self.items.has(resource=resource):
                raise InvalidActionException(f"Cannot change '{resource}' which is not present in the list")
            self.items.get(resource=resource).amount = amount

    def getPopulation(self):
        return self.getAmount("res-populace")

    def getWork(self):
        return self.getAmount("res-prace")

    def getObyvatel(self):
        return self.getAmount("res-obyvatel")

class MaterialStorage(ImmutableModel):
    class MaterialStorageManager(models.Manager):
        def createInitial(self):
            return self.create(items=[])

    objects = MaterialStorageManager()
    items = ListField(model_type=ResourceStorageItem)

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

    def receiveMaterials(self, materials, capacity):
        for resource, amount in materials.items():
            targetAmount = min(self.getAmount(resource) + amount, capacity)
            self.setAmount(resource, targetAmount)

    def getAll(self):
        return {item.resource: item.amount for item in filter(lambda item: item.amount > 0, self.items)}

    def toJson(self):
        return {
            r.resource.id: r.amount for r in self.items
        }

    def godUpdate(self, update):
        for resource, amount in update["add"].items():
            if self.items.has(resource=resource):
                raise InvalidActionException(f"Cannot add '{resource}' which is already present in the list")
            self.items.append(ResourceStorageItem(resource=ResourceModel.objects.get(id=resource), amount=amount))

        for resource, _ in update["remove"].items():
            if not self.items.has(resource=resource):
                raise InvalidActionException(f"Cannot remove '{resource}' which is not present in the list")
            self.items.remove(self.items.get(resource=resource))

        for resource, amount in update["change"].items():
            if not self.items.has(resource=resource):
                raise InvalidActionException(f"Cannot change '{resource}' which is not present in the list")
            self.items.get(resource=resource).amount = amount

    def payResources(self, resources):
        """Subtract resources from storage.

        Returns a dict of resources not tracked by storage"""
        missing = {}
        for resource, amount in resources.items():
            owned = self.getAmount(resource)
            if owned < amount:
                missing[resource] = amount - owned
        if len(missing) > 0:
            raise ResourceStorage.NotEnoughResourcesException("Missing resources", missing)
        result = {}
        for resource, amount in resources.items():
            self.setAmount(resource, self.getAmount(resource) - amount)
        return result

class TechStatusEnum(enum.Enum):
    UNKNOWN = 0 # used only for status check; Never stored in DB
    RESEARCHING = 2
    OWNED = 3

    __labels__ = {
        UNKNOWN: "Neznámý",
        RESEARCHING: "Zkoumá se",
        OWNED: "Vyzkoumaný"
    }

def parseTechStatus(s):
    s = s.strip()
    for option in [TechStatusEnum.UNKNOWN, TechStatusEnum.RESEARCHING, TechStatusEnum.OWNED]:
        if s == option.label:
            return option
    s = s.upper()
    if s == "UKNOWN":
        return TechStatusEnum.UNKNOWN
    if s == "RESEARCHING":
        return TechStatusEnum.RESEARCHING
    if s == "OWNED":
        return TechStatusEnum.OWNED

class TechStorageItem(ImmutableModel):
    tech = models.ForeignKey("TechModel", on_delete=models.PROTECT)
    status = enum.EnumField(TechStatusEnum)
    def __str__(self):
        return self.tech.label + (":❌" if self.status == TechStatusEnum.RESEARCHING else ":✅")

class TechStorage(ImmutableModel):
    class TechStorageManager(models.Manager):
        def createInitial(self, team):
            initialTechs = ["build-centrum", "build-lovci", "tech-hnojeni", "tech-astronomie"]
            if team.id == 2:
                initialTechs += ["build-dul", "tech-uhli", "build-uhlirstvi"]
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

    def availableVyrobas(self):
        vyrobas = []
        for tech in self.items:
            if tech.status != TechStatusEnum.OWNED:
                continue
            vyrobas += tech.tech.unlock_vyrobas.all()
        return vyrobas

    def availableEnhancements(self, vyroba):
        enhs = []
        for tech in self.items:
            if tech.status != TechStatusEnum.OWNED:
                continue
            for e in tech.tech.unlock_enhancers.all():
                if e.vyroba == vyroba:
                    enhs.append(e)
            enhs += [e for e in tech.tech.unlock_enhancers.all() if e.vyroba == vyroba.id]
        return enhs

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

    def getBuildings(self):
        return [x.tech for x in self.items if x.status == TechStatusEnum.OWNED and x.tech.isBuilding]

    def toJson(self):
        return {
            t.tech.id: t.status.label for t in self.items
        }

    def godUpdate(self, update):
        for techId, status in update["add"].items():
            if self.items.has(tech=techId):
                raise InvalidActionException(f"Cannot add '{techId}' which is already present in the list")
            tech = TechModel.objects.get(id=techId)
            self.items.append(TechStorageItem(tech=tech, status=parseTechStatus(status)))

        for tech, _ in update["remove"].items():
            if not self.items.has(tech=tech):
                raise InvalidActionException(f"Cannot remove '{tech}' which is not present in the list")
            self.items.remove(self.items.get(tech=tech))

        for tech, status in update["change"].items():
            if not self.items.has(tech=tech):
                raise InvalidActionException(f"Cannot change '{tech}' which is not present in the list")
            self.items.get(tech=tech).status = parseTechStatus(status)

class VlivStorageItem(ImmutableModel):
    team = models.ForeignKey("Team", on_delete=models.PROTECT)
    amount = models.IntegerField(default=0)

class VlivStorage(ImmutableModel):
    class VlivStorageManager(models.Manager):
        def createInitial(self):
            return self.create(items=[])

    objects = VlivStorageManager()
    items = ListField(model_type=VlivStorageItem)

    def addVliv(self, team, amount):
        self.setVliv(team, self.getVliv(team) + amount)

    def setVliv(self, team, amount):
        assert isinstance(team, Team), f"Neznamy tym: {team}"

        item = None
        try:
            item = self.items.get(team=team)
            item.amount = amount
        except VlivStorageItem.DoesNotExist:
            item = VlivStorageItem(team=team, amount=amount)
            self.items.append(item)
            return

    def getVliv(self, team):
        assert isinstance(team, Team), f"Neznamy tym: {team}"
        try:
            item = self.items.get(team=team)
            return item.amount
        except VlivStorageItem.DoesNotExist:
            return 0



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

    def toJson(self):
        return {
            "population": self.population,
            "work": self.work
        }

    def godUpdate(self, update):
        allowKeys(["population", "work"], update["change"])
        allowKeys([], update["add"])
        allowKeys([], update["remove"])
        if "population" in update["change"]:
            self.population = update["change"]["population"]
        if "work" in update["change"]:
            self.work = update["change"]["work"]

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

    def toJson(self):
        return self.data

    def godUpdate(self, update):
        allowKeys(["counter"], update["change"])
        allowKeys([], update["add"])
        allowKeys([], update["remove"])
        if "counter" in update["change"]:
            self.data["counter"] = update["change"]["counter"]

