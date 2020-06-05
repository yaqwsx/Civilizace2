from django.db import models
from django_enumfield import enum

from game.data import TechModel, ResourceModel, ResourceTypeModel
from game.data.entity import AchievementModel
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
            return self.create(generation=generation)

    objects = WorldStateManager()

    data = JSONField()
    generation = models.IntegerField()

    def __str__(self):
        return json.dumps(self._dict)

    def toJson(self):
        return {
            "generation": self.generation
        }

    def godUpdate(self, update):
        allowKeys(["generation"], update["change"])
        allowKeys([], update["add"])
        allowKeys([], update["remove"])
        if "generation" in update["change"]:
            self.generation = update["change"]["generation"]

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

    def toJson(self):
        return {
            "population": self.population.toJson(),
            "sandbox": self.sandbox.toJson(),
            "turn": self.turn,
            "resources": self.resources.toJson(),
            "techs": self.techs.toJson(),
            "distances": self.distances.toJson(),
            "achievements": self.achievements.toJson()
        }

    def godUpdate(self, update):
        fields = ["population", "sandbox", "resources", "techs", "distances", "achievements"]
        allowKeys(fields + ["turn"], update["change"])
        allowKeys(fields, update["add"])
        allowKeys(fields, update["remove"])
        self.population.godUpdate(eatUpdatePrefixAll("population", update))
        self.sandbox.godUpdate(eatUpdatePrefixAll("sandbox", update))
        self.resources.godUpdate(eatUpdatePrefixAll("resources", update))
        self.techs.godUpdate(eatUpdatePrefixAll("techs", update))
        print("There", update)
        self.achievements.godUpdate(eatUpdatePrefixAll("achievements", update))

        if "turn" in update["change"]:
            turn = update["change"]["turn"]

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
                print("adding")
                self.list.append(AchievementModel.objects.get(id=id))
            except AchievementModel.DoesNotExist:
                raise InvalidActionException(f"Unknown id '{id}'")
        for id in update["remove"].get("", []):
            if not self.list.has(id=id):
                raise InvalidActionException(f"Cannot remove '{id}' which is not present in the list")
            self.list.remove(self.list.get(id=id))

class DistanceItemProductions(ImmutableModel):
    source = models.ForeignKey("ResourceModel", on_delete=models.PROTECT, related_name="distance_source")
    target = models.ForeignKey("TechModel", on_delete=models.PROTECT, related_name="distance_target")
    distance = models.IntegerField()

    def __str__(self):
        return f"{self.source} -> {self.target}={self.distance}"

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

    def getProductionDistance(self, source, target):
        if isinstance(source, str):
            source = ResourceModel.objects.get(id=source)
        if isinstance(target, str):
            target = TechModel.objects.get(id=target)
        items = list(filter(
            lambda item: (item.source == source and item.target == target),
            self.productions
        ))
        assert len(items) <= 1, f"There are multiple distance records for {source} -> {target}"
        if not len(items):
            return MAX_DISTANCE
        return items[0].distance

    def setProductionDistance(self, source, target, distance):
        if isinstance(source, str):
            source = ResourceModel.objects.get(id=source)
        if isinstance(target, str):
            target = TechModel.objects.get(id=target)

        items = list(filter(
            lambda item: (item.source == source and item.target == target),
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

    def toJson(self):
        return {
            "productions": {
                f"{p.source.id} -> {p.target.id}": p.distance for p in self.productions
            },
            "teams": {
                f"{t.team.name}({t.team.id})": t.distance for t in self.teams
            }
        }

    def godUpdate(self, update):
        allowKeys(["productions", "teams"], update["change"])
        allowKeys(["productions", "teams"], update["add"])
        allowKeys(["productions", "teams"], update["remove"])
        self.godUpdateProductions(eatUpdatePrefixAll("productions", update))
        self.godUpdateTeams(eatUpdatePrefixAll("teams", update))

    def godUpdateProductions(self, update):
        def extractResources(s):
            x = s.split(s, "->")
            return x[0].strip(), x[1].strip()
        for desc, value in update["add"].items():
            source, target = extractResources(desc)
            if self.productions.has(source=source, target=target):
                    raise InvalidActionException(f"Cannot add duplicite distance for '{desc}'")
            self.productions.append(DistanceItemProductions(source=source, target=target, distance=value))

        for desc, value in update["remove"].items():
            source, target = extractResources(desc)
            if not self.productions.has(source=source, target=target):
                raise InvalidActionException(f"Cannot change '{desc}' which is not present in the list")
            self.productions.get(source=source, target=target).distance = value

        for desc, value in update["remove"].items():
            source, target = extractResources(desc)
            if not self.productions.has(source=source, target=target):
                raise InvalidActionException(f"Cannot remove '{desc}' which is not present in the list")
            self.productions.remove(self.productions.get(source=source, target=target))

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

    def toJson(self):
        return {
            r.resource.id: r.amount for r in self.items
        }

    def godUpdate(self, update):
        for resource, amount in update["add"].items():
            if self.items.has(resource=resource):
                raise InvalidActionException(f"Cannot add '{resource}' which is already present in the list")
            self.items.append(ResourceStorageItem(resource=resource, amount=amount))

        for resource, _ in update["remove"].items():
            if not self.items.has(resource=resource):
                raise InvalidActionException(f"Cannot remove '{resource}' which is not present in the list")
            self.items.remove(self.items.get(resource=resource))

        for resource, amount in update["change"].items():
            if not self.items.has(resource=resource):
                raise InvalidActionException(f"Cannot change '{resource}' which is not present in the list")
            self.items.get(resource=resource).amount = amount



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

    def toJson(self):
        return {
            t.tech.id: t.status.label for t in self.items
        }

    def godUpdate(self, update):
        for tech, status in update["add"].items():
            if self.items.has(tech=tech):
                raise InvalidActionException(f"Cannot add '{tech}' which is already present in the list")
            self.items.append(TechStorageItem(tech=tech, status=parseTechStatus(status)))

        for tech, _ in update["remove"].items():
            if not self.items.has(tech=tech):
                raise InvalidActionException(f"Cannot remove '{tech}' which is not present in the list")
            self.items.remove(self.items.get(tech=tech))

        for tech, status in update["change"].items():
            if not self.items.has(tech=tech):
                raise InvalidActionException(f"Cannot change '{tech}' which is not present in the list")
            self.items.get(tech=tech).status = parseTechStatus(status)

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

