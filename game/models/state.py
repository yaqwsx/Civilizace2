import math
from django.db import models
from django.db.models.fields import related
from django_enumfield import enum

from game.data import TechModel, ResourceModel, ResourceTypeModel
from game.data.entity import AchievementModel, EntityModel, IslandModel, TaskModel
from game.data.parser import Parser
from game.parameters import INITIAL_POPULATION, MAX_DISTANCE
from .fields import JSONField, ListField
from .immutable import ImmutableModel

import game.managers
import json

from .translations import Translations

from game.managers import PrefetchManager
from game.models.actionBase import ActionEvent, InvalidActionException
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
        super(StateManager, self).__init__(prefetch_related=("teamStates","islandStates"), select_related=("action",))

    def initialParameters(self):
        return {
            "islandExplorePrice": {
                "mat-sklo": 5,
                "mat-sroub": 8,
            },
            "islandColonizePrice": {
                "mat-sklo": 5,
                "mat-sroub": 8,
            },
            "islandColonizeDots": 42,
            "islandRepairPrice": {
                "mat-sklo": 5,
                "mat-sroub": 8,
            },
        }

    def createInitial(self, context):
        teamStates = [TeamState.objects.createInitial(team=team, context=context)
                      for team in Team.objects.all()]
        islandStates = [IslandState.objects.createInitial(islandId=isl.id, context=context)
                      for isl in context.islands.all()]
        worldState = WorldState.objects.createInitial(context)
        action = ActionEvent.objects.createInitial(context)
        state = self.create(action=action, worldState=worldState, parameters=self.initialParameters())
        state.teamStates.set(teamStates)
        state.islandStates.set(islandStates)
        return state

    def getNewest(self):
        state = self.latest("pk")
        state.setContext(state.action.action.context)
        return state

class StateModel(ImmutableModel):
    class Meta:
        abstract = True

    def setContext(self, context):
        self.context = context
        relevantFields = []
        for field in self._meta.get_fields():
            if not hasattr(self, field.name):
                continue
            attr = getattr(self, field.name)
            if isinstance(field, models.fields.related.ManyToManyField):
                for relative in attr.all():
                    relevantFields.append(relative)
            else:
                relevantFields.append(attr)
        for f in relevantFields:
            if hasattr(f, "setContext"):
                f.setContext(context)

    def toEntity(self, id):
        # Not sure if ideal... but what the heck. The whole "prefixy" thing is
        # shady anyway.
        prefixes = {
            "die-": "dies",
            "ach-": "achivements",
            "is-": "island",
            "res-": "resources",
            "mat-": "resources",
            "tech-": "techs",
            "build-": "techs",
            "vyr-": "vyrobas",
            "edge-": "edges",
        }
        for p, c in prefixes.items():
            if id.startswith(p):
                return getattr(self.context, c).get(id=id)
        raise RuntimeError(f"No manager in context for entity {id}")

class State(StateModel):
    action = models.ForeignKey("ActionEvent", on_delete=models.PROTECT)
    worldState = models.ForeignKey("WorldState", on_delete=models.PROTECT)
    teamStates = models.ManyToManyField("TeamState")
    islandStates = models.ManyToManyField("IslandState")

    parameters = JSONField()

    objects = StateManager()

    def teamState(self, teamId):
        if isinstance(teamId, Team):
            teamId = teamId.id
        for ts in self.teamStates.all():
            if ts.team.id == teamId:
                return ts
        return None

    def teamIslands(self, teamId):
        if isinstance(teamId, Team):
            teamId = teamId.id
        return [iss for iss in self.islandStates.all()
                    if iss.owner and iss.owner.id == teamId]

    def islandState(self, islandId):
        if isinstance(islandId, IslandModel):
            islandId = islandId.id
        for iss in self.islandStates.all():
            if iss.island.id == islandId:
                return iss
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
        json.update({
            f"{iss.island.label}({iss.island.id})" : iss.toJson() for iss in self.islandStates.all()
        })
        json["parameters"] = self.parameters
        return json

    def godUpdate(self, update):
        self.worldState.godUpdate(eatUpdatePrefixAll("worldState", update))
        for ts in self.teamStates.all():
            # ToDo: Ignore the team name
            ts.godUpdate(eatUpdatePrefixAll(f"{ts.team.name}({ts.team.id})", update))
        for iss in self.islandStates.all():
            # ToDo: Ignore the island name
            iss.godUpdate(eatUpdatePrefixAll(f"{iss.island.label}({iss.island.label})", update))
        if "parameters" in update["change"]["parameters"]:
            self.parameters = update["change"]["parameters"]

    def getPrice(self, name, multiplicator=1):
        """
        Given a name of a price in parameters, return it as a map from entities
        to amounts.
        """
        return { self.toEntity(entId): amount * multiplicator
            for entId, amount in self.parameters[name].items()}


class WorldState(StateModel):
    class WorldStateManager(models.Manager):
        def createInitial(self, context):
            generation = 1
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

class TeamState(StateModel):
    class TeamStateManager(models.Manager):
        def createInitial(self, team, context):
            return self.create(
                team=team,
                sandbox=SandboxTeamState.objects.createInitial(context),
                population=PopulationTeamState.objects.createInitial(context),
                turn=0,
                resources=ResourceStorage.objects.createInitial(team, context),
                materials=MaterialStorage.objects.createInitial(context),
                techs=TechStorage.objects.createInitial(["build-centrum"], context),
                distances=DistanceLogger.objects.createInitial(team, context),
                achievements=TeamAchievements.objects.createInitial(context),
                foodSupply=FoodStorage.objects.createInitial(context),
                discoveredIslandsList=[],
                exploredIslandsList=[])

    objects = TeamStateManager()

    team = models.ForeignKey("Team", on_delete=models.PROTECT)
    population = models.ForeignKey("PopulationTeamState", on_delete=models.PROTECT)
    sandbox = models.ForeignKey("SandboxTeamState", on_delete=models.PROTECT)
    turn = models.IntegerField()
    resources = models.ForeignKey("ResourceStorage", on_delete=models.PROTECT, related_name="resources")
    materials = models.ForeignKey("MaterialStorage", on_delete=models.PROTECT, related_name="materials")
    techs = models.ForeignKey("TechStorage", on_delete=models.PROTECT, related_name="techs")
    distances = models.ForeignKey("DistanceLogger", on_delete=models.PROTECT)
    achievements = models.ForeignKey("TeamAchievements", on_delete=models.PROTECT)
    foodSupply = models.ForeignKey("FoodStorage", on_delete=models.PROTECT)

    discoveredIslandsList = JSONField()
    exploredIslandsList = JSONField()

    def __str__(self):
        return "<TeamState " + json.dumps(self._dict) + ">"

    def nextTurn(self):
        self.turn += 1

    @property
    def discoveredIslands(self):
        """ Get models of discovered islands """
        return [self.context.islands.get(id=id) for id in self.discoveredIslandsList]

    @property
    def exploredIslands(self):
        """ Get models of explored islands """
        return [self.context.islands.get(id=id) for id in self.exploredIslandsList]

    def addDiscoveredIsland(self, island):
        assert isinstance(island, str)
        self.discoveredIslandsList.append(island)
        self.discoveredIslandsList = list(set(self.discoveredIslandsList))

    def addExploredIsland(self, island):
        assert isinstance(island, str)
        self.exploredIslandsList.append(island)
        self.exploredIslandsList = list(set(self.exploredIslandsList))

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
            "materials": self.materials.toJson(),
            "discoveredIslands": self.discoveredIslandsList,
            "exploredIslands": self.exploredIslandsList
        }

    def godUpdate(self, update):
        fields = ["population", "sandbox", "resources", "techs",
                  "distances", "achievements", "foodSupply", "materials",
                  "discoveredIslands", "exploredIslands"]
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
        self.distances.godUpdate(eatUpdatePrefixAll("distances", update))

        if "turn" in update["change"]:
            self.turn = update["change"]["turn"]
        if "discoveredIslands" in update["change"]:
            self.discoveredIslandsList = update["change"]["discoveredIslands"]
        if "exploredIslands" in update["change"]:
            self.exploredIslandsList = update["change"]["exploredIslands"]

class IslandState(StateModel):
    class InslandManager(models.Manager):
        def createInitial(self, islandId, context):
            root = context.islands.get(id=islandId).root.id
            return self.create(
                islandId=islandId,
                owner=None,
                techs=TechStorage.objects.createInitial([root], context),
                defense=0)

    objects = InslandManager()

    islandId = models.CharField(max_length=32)
    owner = models.ForeignKey("Team", on_delete=models.PROTECT, related_name="owened_islands", null=True)
    techs = models.ForeignKey("TechStorage", on_delete=models.PROTECT)
    defense = models.IntegerField()

    @property
    def island(self):
        return self.context.islands.get(id=self.islandId)

    @property
    def maxDefense(self):
        return sum(map(lambda x: x.defenseBonus, self.techs.getOwnedTechs()))

    def toJson(self):
        return {
            "owner": self.owner.id if self.owner else None,
            "techs": self.techs.toJson(),
            "defense": self.defense
        }


class TeamAchievements(StateModel):
    class TeamAchievementsManager(models.Manager):
        def createInitial(self, context):
            return self.create(list=[])

    list = ListField(model_type=AchievementModel)
    objects = TeamAchievementsManager()

    def awardNewAchievements(self, state, team):
        """ Checks if new achievements should be awarded, if so, return their list """
        newAchievements = []
        for achievement in self.context.achievements.all():
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
                self.list.append(self.context.achievements.get(id=id))
            except AchievementModel.DoesNotExist:
                raise InvalidActionException(f"Unknown id '{id}'")
        for id in update["remove"].get("", []):
            if not self.list.has(id=id):
                raise InvalidActionException(f"Cannot remove '{id}' which is not present in the list")
            self.list.remove(self.list.get(id=id))


class DistanceItemBuilding(StateModel):
    source = models.ForeignKey("TechModel", on_delete=models.PROTECT, related_name="distance_source")
    target = models.ForeignKey("TechModel", on_delete=models.PROTECT, related_name="distance_target")
    distance = models.IntegerField()

    def __str__(self):
        return f"{self.source} -> {self.target}={self.distance}"

class DistanceItemTeams(StateModel):
    team = models.ForeignKey("Team", on_delete=models.PROTECT)
    distance = models.IntegerField()

class MissingDistanceError(RuntimeError):
    def __init__(self, msg, source, target):
        super().__init__(msg)
        self.source = source
        self.target = target

class DistanceLogger(StateModel):
    class DistanceLoggerManager(models.Manager):
        def createInitial(self, team, context):
            result = self.create(building=[], teams=[])
            return result
    objects = DistanceLoggerManager()

    building = ListField(model_type=DistanceItemBuilding)
    teams = ListField(model_type=DistanceItemTeams)

    def getBuildingDistance(self, source, target):
        if isinstance(source, str):
            source = self.context.techs.get(id=source)
        if isinstance(target, str):
            target = self.context.techs.get(id=target)
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
            source = self.context.techs.get(id=source)
        if isinstance(target, str):
            target = self.context.techs.get(id=target)
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
            x = s.split("->")
            return x[0].strip(), x[1].strip()
        for desc, value in update["add"].items():
            source, target = extractResources(desc)
            if self.building.has(source=source, target=target):
                    raise InvalidActionException(f"Cannot add duplicite distance for '{desc}'")
            self.building.append(DistanceItemBuilding(source=source, target=target, distance=value))

        for desc, value in update["change"].items():
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

        for desc, value in update["change"].items():
            id = extractTeamId(desc)
            if not self.teams.has(team=id):
                raise InvalidActionException(f"Cannot change '{id}' which is not present in the list")
            self.teams.get(team=id).distance = value

        for desc, value in update["remove"].items():
            id = extractTeamId(desc)
            if not self.teams.has(team=id):
                raise InvalidActionException(f"Cannot remove '{id}' which is not present in the list")
            self.teams.remove(self.teams.get(team=id))

class FoodStorageItem(StateModel):
    resource = models.ForeignKey("ResourceModel", on_delete=models.PROTECT)
    amount = models.IntegerField()

class Storage(StateModel):
    class Meta:
        abstract = True

    class StorageManager(models.Manager):
        def createInitial(self, context):
            return self.create(items={})

    objects = StorageManager()
    items = JSONField()

    def setContext(self, context):
        self.context = context

    def count(self):
        sum = 0
        for _, val in self.items():
            sum += val
        return sum

    def get(self, id):
        """
        Get amount of entity stored
        """
        if isinstance(id, EntityModel):
            id = id.id
        assert isinstance(id, str)
        try:
            return self.items[id]
        except KeyError:
            return 0

    def set(self, id, value):
        """
        Set amount of entity stored.
        """
        if isinstance(id, EntityModel):
            id = id.id
        assert isinstance(id, str)
        self.items[id] = value

    def asMap(self):
        """
        Return a map that maps Entity models to the amounts stored
        """
        return { self.toEntity(id): amount for id, amount in self.items.items() if amount > 0}

    def toJson(self):
        return self.items

    def godUpdate(self, update):
        for resource, amount in update["add"].items():
            self.items[resource] = amount

        for resource, _ in update["remove"].items():
            del self.items[resource]

        for resource, amount in update["change"].items():
            self.items[resource] = amount

class FoodStorage(StateModel):
    class FoodStorageManager(models.Manager):
        def createInitial(self, context):
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
        luxusSums = [sum(luxusAmounts[n:]) for n in range(7)]
        result = []

        for kasta in populaceKast:
            popSum += kasta[1]
            foodSupply = foodSums[0]
            qualitySupply = foodSums[kasta[0]]
            luxusSupply = luxusSums[kasta[0]]
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
        return self.getSupply(self.context.resourceTypes.get(id="type-jidlo"))

    def getLuxusSupply(self):
        return self.getSupply(self.context.resourceTypes.get(id="type-luxus"))

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
        # Maara should delete this once he updates food storage
        return []

    def godUpdate(self, update):
        # Maara should delete this once he updates food storage
        return

class ResourceStorageAbstract(Storage):
    class Meta:
        abstract = True

    class NotEnoughResourcesException(InvalidActionException):
        def __init__(self, msg, list):
            super().__init__(msg + '<ul>' + "".join([f'{amount}x {res.label}' for res, amount in list.items()]) + '</ul>')
            self.list = list

    class ResourceStorageManager(models.Manager):
        def createInitial(self, team, context):
            initialResources = [("res-obyvatel", INITIAL_POPULATION), ("res-prace", INITIAL_POPULATION), ("res-populace", INITIAL_POPULATION)]
            items = {}
            for id, amount in initialResources:
                items[id] = amount
            result = self.create(items=items)
            return result

    objects = ResourceStorageManager()

    def ignored(self, resource):
        return resource.id[:4] == "mat-"

    @staticmethod
    def asHtml(resources, separator=", "):
        if len(resources) > 0:
            return separator.join([
               f'{value}&times; {key.htmlRepr()}'
               for key, value in resources.items()])
        return "-"

    def __str__(self):
        list = [resource.label + ":" + str(label) for resource, label in self.asMap().items()]
        result = ", ".join(list)
        return result

    def set(self, resource, amount):
        if (resource.id == "res-obyvatel"):
            diff = self.get(resource) - amount
            super().add("res-populace", diff)
        super().set(resource, amount)

    def add(self, resource, amount):
        newAmount = self.get(resource) + amount
        if newAmount < 0: raise ResourceStorage.NotEnoughResourcesException("Cannot lower resource amount below 0", [(resource, amount)])
        self.set(resource, newAmount)

    def spendWork(self, amount):
        self.payResources({self.context.resources.get(id="res-prace"): amount})

    def hasResources(self, resources):
        for resource, amount in resources.items():
            if self.ignored(resource):
                continue
            if self.get(resource) < amount:
                return False
        return True

    def payResources(self, resources):
        """Subtract resources from storage.

        Returns a dict of resources not tracked by storage"""
        missing = {}
        for resource, amount in resources.items():
            if self.ignored(resource):
                continue
            owned = self.get(resource)
            if owned < amount:
                missing[resource] = amount - owned
        if len(missing) > 0:
            raise ResourceStorage.NotEnoughResourcesException("Missing resources", missing)
        result = {}
        for resource, amount in resources.items():
            if self.ignored(resource):
                result[resource] = amount
            else:
                self.add(resource, -amount)
        return result

    def receiveResources(self, resources):
        """Add resources to storage.

        Returns a dict of resources not tracked by storage"""
        result = {}
        for resource, amount in resources.items():
            if self.ignored(resource):
                result[resource] = amount
            else:
                targetAmount = self.get(resource) + amount
                self.set(resource, targetAmount)
        return result

    def returnResources(self, resources):
        """Return resources to storage.

        Returns a dict of resources not tracked by storage"""
        result = {}
        for resource, amount in resources.items():
            if self.ignored(resource):
                result[resource] = amount
            else:
                self.add(resource, amount)
        return result

    def getResourcesByType(self, metaResource=None):
        resourceType = metaResource.type if metaResource else None
        level = metaResource.level if metaResource else 2
        isProduction = metaResource.isProduction if metaResource else True

        results = {}
        for resource, amount in self.asMap().items():
            if amount == 0:
                continue
            if ((not resourceType) or resource.type == resourceType)\
                    and resource.level >= level \
                    and resource.isProduction == isProduction:
                results[resource] = amount
        return results

    def getPopulation(self):
        return self.get("res-populace")

    def getWork(self):
        return self.get("res-prace")

    def getObyvatel(self):
        return self.get("res-obyvatel")

class ResourceStorage(ResourceStorageAbstract):
    pass

class MaterialStorage(ResourceStorageAbstract):
    class MaterialStorageManager(models.Manager):
        def createInitial(self, context):
            return self.create(items={})

    objects = MaterialStorageManager()

    def ignored(self, resource):
        return resource.id[:4] != "mat-"

    def receiveMaterials(self, materials, capacity):
        for resource, amount in materials.items():
            targetAmount = min(self.get(resource) + amount, capacity)
            self.set(resource, targetAmount)


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

class TechStorage(Storage):
    class TechStorageManager(models.Manager):
        def createInitial(self, initialTechs, context):
            result = self.create(items={techId: TechStatusEnum.OWNED for techId in initialTechs})
            return result

    objects = TechStorageManager()

    def __str__(self):
        list = [entity.label + ": " + TechStatusEnum(status).label for entity, status in self.asMap().items()]
        result = ", ".join(list)
        return result

    def getStatus(self, tech):
        try:
            result = self.get(tech)
            return result if result else TechStatusEnum.UNKNOWN
        except Exception as e:
            return TechStatusEnum.UNKNOWN

    def setStatus(self, tech, status, enforce=False):
        previousValue = None
        try:
            previousItem = self.get(tech)
        except Exception:
            pass

        if previousItem:
            if status < previousItem:
                raise Exception("Cannot downgrade status of " + tech.label)
            if status == previousItem:
                return previousItem
            self.items.pop(tech.id)

        self.set(tech.id, status)
        return

    def getOwnedTechs(self):
        return [self.toEntity(tech) for tech, status
                    in self.items.items()
                    if status == TechStatusEnum.OWNED]

    def availableVyrobas(self):
        vyrobas = []
        for tech, status in self.asMap().items():
            if status != TechStatusEnum.OWNED:
                continue
            vyrobas += tech.unlock_vyrobas.all()
        return vyrobas

    def getTechsUnderResearch(self):
        return [self.toEntity(tech) for tech, status
                    in self.items.items()
                    if status == TechStatusEnum.RESEARCHING]

    def getActionableEdges(self):
        ownedTechs = self.getOwnedTechs()
        startedTechs = list(map(
            lambda item: item[0],
            filter(
                lambda item: item[1] == TechStatusEnum.RESEARCHING or item[1] == TechStatusEnum.OWNED,
                self.asMap().items())))

        edges = set()
        for tech, status in self.asMap().items():
            for edge in tech.unlocks_tech.all():
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
        return [tech for tech, status in self.asMap().items() if status == TechStatusEnum.OWNED and tech.isBuilding]

    def godUpdate(self, update):
        for techId, status in update["add"].items():
            self.items[techId] = parseTechStatus(status)

        for techId, _ in update["remove"].items():
            del self.items[techId]

        for techId, status in update["change"].items():
            self.items[techId] = parseTechStatus(status)

# =================================================

class PopulationTeamStateManager(models.Manager):
    def createInitial(self, context):
        return self.create(
            work=parameters.INITIAL_POPULATION,
            population=parameters.INITIAL_POPULATION
        )


class PopulationTeamState(StateModel):
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
    def createInitial(self, context):
        return self.create(data={
            "counter": 0
        })


class SandboxTeamState(StateModel):
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

