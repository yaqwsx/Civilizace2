from __future__ import annotations
import enum
from html import entities
import types
import pydantic
from pydantic import BaseModel, PrivateAttr
from typing import List, Dict, Optional, Iterable, Union, Set
from decimal import Decimal
from game.actions.common import ActionException
from game.entities import *

class StateModel(BaseModel):
    _parent: Optional[StateModel]=PrivateAttr()

    def __eq__(self, other: Any) -> bool:
        if self.__class__ != other.__class__:
            return False
        for field in self.__fields__.values():
            if getattr(self, field.name) != getattr(other, field.name):
                return False
        return True

    # By default, pydantic makes a copy of models on validation. We want to
    # avoid this as state is shared. Therefore, we override the behavior
    @classmethod
    def validate(cls: types['pydantic.Model'], value: Any) -> 'pydantic.Model':
        if isinstance(value, cls):
            return value # This is the changed behavior
        return super().validate(cls, value)

    def _setParent(self, parent: Optional[BaseModel]=None):
        self._parent = parent

class ArmyState(enum.Enum):
    Idle = 0
    Marching = 1
    Occupying = 2

class ArmyGoal(enum.Enum):
    Occupy = 0
    Eliminate = 1
    Supply = 2
    Replace = 3


class ArmyId(BaseModel):
    prestige: int
    team: Team

    def __hash__(self):
        return self.team.__hash__() + self.prestige

    def __eq__(self, other):
        if type(other) != type(self):
            return False
        return self.team == other.team and self.prestige == other.prestige

class Army(StateModel):
    team: Team # duplicates: items in Team.armies
    prestige: int
    equipment: int=0 # number of weapons the army currently carries
    boost: int=-1 # boost added by die throw
    tile: Optional[MapTileEntity]=None
    state: ArmyState=ArmyState.Idle
    goal: Optional[ArmyGoal]=None

    @property
    def parent(self) -> TeamState:
        assert isinstance(self._parent, TeamState)
        return self._parent

    @property
    def capacity(self) -> int:
        return self.prestige - BASE_ARMY_STRENGTH

    @property
    def id(self) -> ArmyId:
        return ArmyId(prestige=self.prestige, team=self.team)

    @property
    def strength(self) -> int:
        return self.equipment + BASE_ARMY_STRENGTH + max(0, self.boost)

    @property
    def isMarching(self) -> bool:
        return self.tile == None

    @property
    def isBoosted(self) -> bool:
        return self.boost >= 0

    def retreat(self, state: GameState) -> int:
        result = self.equipment
        tile = state.map.tiles[self.tile.index]
        if self.state == ArmyState.Occupying:
            assert tile.occupiedBy == self.id, "Army {} thinks its occupying a tile occupied by {}".format(self.id, tile.occupiedBy)
            tile.occupiedBy = None
        tile.inbound.discard(self.id)

        self.state = ArmyState.Idle
        self.equipment = 0
        self.boost = -1
        self.tile = None
        self.goal = None
        return result

    def occupy(self, tile: MapTile):
        if tile.occupiedBy == self.id: return
        assert tile.occupiedBy == None, "Nelze obsadit pole obsazené cizí armádou"
        tile.occupiedBy = self.id
        tile.inbound.discard(self.id)

        self.state = ArmyState.Occupying
        self.boost = -1
        self.tile = tile.entity
        self.goal = None

    def destroyEquipment(self, casualties: int) -> int:
        self.equipment = max(0, self.equipment - casualties)
        return BASE_ARMY_STRENGTH + self.equipment


class MapTile(StateModel): # Game state elemnent
    entity: MapTileEntity
    occupiedBy: Optional[ArmyId]=None
    buildings: Dict[Building, Optional[TeamId]]={} # TeamId is stored for stats purposes only
    inbound: Set[ArmyId]=set()

    @property
    def parent(self) -> MapState:
        assert isinstance(self._parent, MapState)
        return self._parent

    @property
    def name(self) -> str:
        return self.entity.name

    @property
    def index(self) -> int:
        return self.entity.index

    @property
    def parcelCount(self) -> int:
        return self.entity.parcelCount

    @property
    def richness(self) -> int:
        return self.entity.richness

    @property
    def features(self) -> List[TileFeature]:
        return self.entity.naturalResources + self.buildings.keys()

    @property
    def id(self) -> EntityId:
        return self.entity.id

    @property
    def defenseBonus(self) -> int:
        return 0

    @property
    def occupyingArmyState(self) -> Optional[Army]:
        return None
        # if self.occupiedBy == None:
        #     return None
        # self.parent.parent.teams[self.occupiedBy.team].

class HomeTile(MapTile):
    team: Team
    roadsTo: List[MapTileEntity]=[]

    @classmethod
    def createInitial(cls, team: Team, tile: MapTileEntity, entities: Entities) -> HomeTile:
        return HomeTile(name="Domovské pole " + team.name,
                       index=tile.index,
                       parcelCount=3,
                       richness=0,
                       naturalResources = tile.naturalResources)


class MapState(StateModel):
    size: int=MAP_SIZE
    tiles: Dict[int, MapTile]
    homeTiles: Dict[Team, HomeTile]

    def _setParent(self, parent: Optional[BaseModel]=None):
        self._parent = parent
        for t in self.tiles.values():
            t._setParent(self)
        for t in self.homeTiles.values():
            t._setParent(self)

    @property
    def parent(self) -> GameState:
        assert isinstance(self._parent, GameState)
        return self._parent

    def _getRelativeIndex(self, team: Team, tile: MapTileEntity) -> int:
        home = self.homeTiles[team]
        assert home != None, "Team {} has no home tile".format(team.id)
        relIndex = tile.index - home.index
        relIndexOffset = relIndex + self.size/2
        return (relIndexOffset % self.size) - self.size/2

    def getRawDistance(self, team: Team, tile: MapTileEntity) -> Decimal:
        relativeIndex = self._getRelativeIndex(team, tile)
        assert relativeIndex in TILE_DISTANCES_RELATIVE, "Tile {} is unreachable for {}".format(tile, team.id)
        return TILE_DISTANCES_RELATIVE[relativeIndex] * TIME_PER_TILE_DISTANCE

    def getActualDistance(self, team: Team, tile: MapTileEntity) -> Decimal:
        relativeIndex = self._getRelativeIndex(team, tile)
        assert relativeIndex in TILE_DISTANCES_RELATIVE, "Tile {} is unreachable for {}".format(tile, team.id)
        distance = TILE_DISTANCES_RELATIVE[relativeIndex] * TIME_PER_TILE_DISTANCE
        home = self.homeTiles[team]
        if relativeIndex != tile.index - home.index:
            distance *= Decimal(0.8) # Tiles are around the map
        multiplier = 1
        if tile in home.roadsTo:
            multiplier -= 0.5
        tileState = self.tiles[tile.index]
        if tileState.occupiedBy != None and tileState.occupiedBy.team == team:
            multiplier -= 0.5
        return Decimal(float(distance) * multiplier)

    def getHomeTile(self, team: Team) -> HomeTile:
        return self.homeTiles.get(team)


    @classmethod
    def createInitial(cls, entities: Entities) -> MapState:
        return MapState(
            tiles = {tile.index: MapTile(entity=tile) for tile in entities.tiles.values() if tile.index % 4 != 1},
            homeTiles = {}
        )


class TeamState(StateModel):
    team: Team
    redCounter: Decimal
    blueCounter: Decimal

    turn: int = 0

    techs: Set[Tech]
    researching: Set[Tech] = set()
    armies: Dict[ArmyId, Army]

    resources: Dict[Resource, Decimal]
    storage: Dict[Resource, Decimal]
    granary: Dict[Resource, Decimal] = {}
    storageCapacity = 10

    def _setParent(self, parent: Optional[BaseModel]=None):
        self._parent = parent
        for t in self.armies.values():
            t._setParent(self)

    @property
    def parent(self) -> GameState:
        assert isinstance(self._parent, GameState)
        return self._parent

    def getUnlockingDice(self, entity: EntityWithCost) -> Set[str]:
        dice = set()
        for unlock in entity.unlockedBy:
            if unlock[0] in self.techs:
                dice.add(unlock[1])
        return dice

    def collectStickerEntitySet(self) -> set[Entity]:
        stickers = set()
        stickers.update(self.techs)
        stickers.update(self.vyrobas)
        return stickers


    def _addEmployees(self, amount: int) -> None:
        for resource in self.resources.keys():
            if resource.id == "res-zamestnanec":
                self.resources[resource] += amount
                return


    def payResources(self, resources: Dict[Resource, Decimal]) -> Dict[Resource, Decimal]:
        tokens = {}
        missing = {}
        for resource, amount in resources.items():
            if resource.isTracked:
                self.resources[resource] = self.resources.get(resource, 0) - amount
                if resource.id == "res-obyvatel":
                    self._addEmployees(amount)
                if self.resources[resource] < 0:
                    missing[resource] = -self.resources[resource]
            else:
                tokens[resource] = amount

        if missing != {}:
            raise ActionException(f"Nemáte dostatek zdrojů. Chybí: [[{printResourceListForMarkdown(missing)}]]")

        return tokens


    def receiveResources(self, resources: Dict[Resource, Decimal], instantWithdraw: bool = False) -> Dict[Resource, Decimal]:
        storage = {}
        for resource, amount in resources.items():
            if resource.isTracked:
                self.resources[resource] = self.resources.get(resource, 0) + amount
            else:
                storage[resource] = amount
        if instantWithdraw:
            return storage
        for resource, amount in storage.items():
            amount = self.storage.get(resource, 0) + amount
            if amount > self.storageCapacity and resource.id != "mat-zbrane":
                amount = self.storageCapacity
            self.storage[resource] = amount
        return {}


    @property
    def vyrobas(self) -> set[Vyroba]:
        vyrobas = set()
        for t in self.techs:
            vyrobas.update(t.unlocksVyrobas)
        return vyrobas

    @property
    def work(self) -> Decimal:
        # TBA: Think of a better way...
        for r, a in self.resources.items():
            if r.id == "res-prace":
                return a
        return 0

    @property
    def population(self) -> int:
        return sum([amount for resource, amount in self.resources.items() if resource.id in ["res-obyvatel", "res-zamestnanec"]])

    @classmethod
    def createInitial(cls, team: Team, entities: Entities) -> TeamState:
        armies = {ArmyId(prestige=x, team=team): Army(team=team, prestige=x) for x in STARTER_ARMY_PRESTIGES}
        return TeamState(
            team=team,
            redCounter=0,
            blueCounter=0,
            techs=[entities["tec-start"]],
            armies=armies,
            resources={
                entities.obyvatel: Decimal(100),
                entities.work: Decimal(100),
                entities["pro-drevo"]: Decimal(20)
            },
            storage={
                entities["mat-drevo"]: Decimal(10)
            }
        )


class GameState(StateModel):
    turn: int
    teamStates: Dict[Team, TeamState]
    map: MapState
    casteCount: int=3

    def _setParent(self) -> None:
        for t in self.teamStates.values():
            t._setParent(self)
        self.map._setParent(self)

    def getArmy(self, id: ArmyId) -> Army:
        return self.teamStates[id.team].armies.get(id) if id != None else None

    @classmethod
    def createInitial(cls, entities: Entities) -> GameState:
        teamStates = {}
        for v in entities.teams.values():
            teamStates[v] = TeamState.createInitial(v, entities)

        return GameState(
            turn=0,
            teamStates={team: TeamState.createInitial(team, entities) for team in entities.teams.values()},
            map=MapState.createInitial(entities)
        )


    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._setParent()


def printResourceListForMarkdown(self, resources: Dict[Resource, Decimal]) -> str:
    return "\n".join([f"1. [[{resource.id}|{{amount}}]]" for resource, amount in resources.items()]) + "\n"
