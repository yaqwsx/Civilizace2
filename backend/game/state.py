from __future__ import annotations
from argparse import ArgumentError
import enum
from html import entities
from statistics import mode
import types
import pydantic
from pydantic import BaseModel, PrivateAttr
from typing import List, Dict, Optional, Iterable, Union, Set
from decimal import Decimal
from game.actions.common import ActionException, ActionFailed, MessageBuilder
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

class ArmyMode(enum.Enum):
    Idle = 0
    Marching = 1
    Occupying = 2

class ArmyGoal(enum.Enum):
    Occupy = 0
    Eliminate = 1
    Supply = 2
    Replace = 3

class Army(StateModel):
    team: Team # duplicates: items in Team.armies
    index: int
    name: str
    level: int
    equipment: int=0 # number of weapons the army currently carries
    boost: int=-1 # boost added by die throw
    tile: Optional[MapTileEntity]=None
    mode: ArmyMode=ArmyMode.Idle
    goal: Optional[ArmyGoal]=None

    @property
    def parent(self) -> MapState:
        assert isinstance(self._parent, MapState)
        return self._parent

    @property
    def capacity(self) -> int:
        return (self.level+2)*5 - BASE_ARMY_STRENGTH

    @property
    def strength(self) -> int:
        return self.equipment + BASE_ARMY_STRENGTH

    @property
    def isMarching(self) -> bool:
        return self.tile == None

    @property
    def isBoosted(self) -> bool:
        return self.boost >= 0

    def destroyEquipment(self, casualties: int) -> int:
        destroyed = min(self.equipment, casualties)
        self.equipment -= destroyed
        return destroyed

    @property
    def currentTile(self):
        if self.mode != ArmyMode.Occupying:
            return None
        return self.tile



class MapTile(StateModel): # Game state element
    entity: MapTileEntity
    unfinished: Dict[Team, Set[Building]]={}
    buildings: Set[Building]=set()
    richnessTokens: int

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
        return self.entity.naturalResources + list(self.buildings)

    @property
    def id(self) -> EntityId:
        return self.entity.id

    @property
    def defenseBonus(self) -> int:
        return 0

    @property
    def occupiedBy(self) -> Optional[Army]:
        return None

    @property
    def inboundArmies(self) -> List[Army]:
        return []


class MapState(StateModel):
    size: int=MAP_SIZE
    tiles: Dict[int, MapTile]
    armies: List[Army]

    def _setParent(self, parent: Optional[BaseModel]=None):
        self._parent = parent
        for t in self.tiles.values():
            t._setParent(self)

    @property
    def parent(self) -> GameState:
        assert isinstance(self._parent, GameState)
        return self._parent

    def getTileById(self, id: str) -> Optional[MapTile]:
        tiles = [tile for tile in self.tiles.values() if tile.id == id]
        if len(tiles) != 1:
            return None
        return tiles[0]

    def getHomeOfTeam(self, team: Team) -> MapTile:
        return self.parent.teamStates[team].homeTile

    def _getRelativeIndex(self, team: Team, tile: MapTileEntity) -> int:
        home = self.getHomeOfTeam(team)
        assert home != None, "Team {} has no home tile".format(team.id)
        relIndex = tile.index - home.index
        relIndexOffset = relIndex + self.size/2
        return round((relIndexOffset % self.size) - self.size/2)

    def getRawDistance(self, team: Team, tile: MapTileEntity) -> Decimal:
        relativeIndex = self._getRelativeIndex(team, tile)
        assert relativeIndex in TILE_DISTANCES_RELATIVE, "Tile {} is unreachable for {}".format(tile, team.id)
        return TILE_DISTANCES_RELATIVE[relativeIndex] * TIME_PER_TILE_DISTANCE

    def getActualDistance(self, team: Team, tile: MapTileEntity) -> Decimal:
        relativeIndex = self._getRelativeIndex(team, tile)
        assert relativeIndex in TILE_DISTANCES_RELATIVE, "Tile {} is unreachable for {}".format(tile, team.id)
        distance = TILE_DISTANCES_RELATIVE[relativeIndex] * TIME_PER_TILE_DISTANCE
        home = self.getHomeOfTeam(team)
        if relativeIndex != tile.index - home.index:
            distance *= Decimal(0.8) # Tiles are around the map
        multiplier = 1
        teamState = self.parent.teamStates[team]
        if tile in teamState.roadsTo:
            multiplier -= 0.5
        if self.getOccupyingTeam(tile) == team:
            multiplier -= 0.5
        return Decimal(float(distance) * multiplier)

    def getReachableTiles(self, team: Team) -> List[MapTileEntity]:
        index = self.getHomeOfTeam(team).index
        indexes = [(index+i) % self.size for i in TILE_DISTANCES_RELATIVE]
        return [self.tiles[i] for i in indexes]

    def getTeamArmies(self, team: Team) -> List[Army]:
        return [army for army in self.armies if army.team == team]

    def getOccupyingArmy(self, tile: MapTileEntity) -> Optional[Army]:
        for army in self.armies:
            if army.tile == tile and army.mode == ArmyMode.Occupying:
                return army
        return None

    def getOccupyingTeam(self, tile: MapTileEntity) -> Optional[Team]:
        for army in self.armies:
            if army.tile == tile:
                return army.team

        for team in self.parent.teamStates.keys():
            if team.homeTileId == tile.id:
                return team
        return None

    def retreatArmy(self, army: Army) -> int:
        result = army.equipment
        tile = self.getTileById(army.tile.id)
        if tile == None:
            return 0

        army.mode = ArmyMode.Idle
        army.equipment = 0
        army.boost = -1
        army.tile = None
        army.goal = None
        return result

    def occupyTile(self, army: Army, tile: MapTile):
        assert self.getOccupyingArmy(tile.entity) == None
        assert army.equipment > 0, "Nevyzbrojená armáda nemůže obsazovat pole"
        assert army.mode != ArmyMode.Occupying
        assert self.getRawDistance(army.team, tile.entity) != None

        army.mode = ArmyMode.Occupying
        army.boost = -1
        army.tile = tile.entity
        army.goal = None


    @classmethod
    def createInitial(cls, entities: Entities) -> MapState:
        armies = []
        teams = entities.teams.values()
        armies.extend([Army(team=team, index=i, name="A", level=3) for i, team in enumerate(teams)])
        armies.extend([Army(team=team, index=i+8, name="B", level=2) for i, team in enumerate(teams)])
        armies.extend([Army(team=team, index=i+16, name="C", level=1) for i, team in enumerate(teams)])

        return MapState(
            tiles = {tile.index: MapTile(entity=tile, richnessTokens=tile.richness) for tile in entities.tiles.values()},
            armies = armies
        )


class PlagueStats(StateModel):
    sick: int = 1
    immune: int = 0

    recovery: float = 0.3
    mortality: float = 0.3
    infectiousness: float = 2.

    recipes: List[str] = []


class TeamState(StateModel):
    team: Team
    redCounter: Decimal
    blueCounter: Decimal

    turn: int = 0
    throwCost: int = 10

    techs: Set[Tech]
    researching: Set[Tech] = set()
    roadsTo: Set[MapTileEntity] = set()

    resources: Dict[Resource, Decimal]
    storage: Dict[Resource, Decimal]
    granary: Dict[Resource, Decimal] = {}
    storageCapacity = 10
    plague: Optional[PlagueStats]

    discoveredTiles: Set[MapTileEntity] = []

    def _setParent(self, parent: Optional[BaseModel]=None):
        self._parent = parent

    @property
    def parent(self) -> GameState:
        assert isinstance(self._parent, GameState)
        return self._parent

    @property
    def homeTile(self) -> MapTile:
        return self.parent.map.getTileById(self.team.homeTileId)


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


    def addEmployees(self, amount: int) -> None:
        for resource in self.resources.keys():
            if resource.id == "res-zamestnanec":
                self.resources[resource] += amount
                return


    @property
    def vyrobas(self) -> set[Vyroba]:
        vyrobas = set()
        for t in self.techs:
            vyrobas.update(t.unlocksVyrobas)
        return vyrobas

    @property
    def buildings(self) -> set[Building]:
        buildings = set()
        for t in self.techs:
            buildings.update(t.unlocksBuilding)
        return buildings

    @property
    def work(self) -> Decimal:
        return self.resources.get(adHocEntitiy("res-prace"), 0)

    @property
    def population(self) -> int:
        return sum([amount for resource, amount in self.resources.items() if resource.id in ["res-obyvatel", "res-zamestnanec"]])

    @property
    def culture(self) -> Decimal:
        return self.resources.get(adHocEntitiy("res-kultura"), 0)

    @classmethod
    def createInitial(cls, team: Team, entities: Entities) -> TeamState:
        return TeamState(
            team=team,
            redCounter=0,
            blueCounter=0,
            techs=[entities["tec-start"]],
            resources={
                entities.obyvatel: Decimal(100),
                entities.work: Decimal(100),
                entities["pro-drevo"]: Decimal(20)
            },
            storage={
                entities["mat-drevo"]: Decimal(10)
            }
        )

class WorldState(StateModel):
    turn: int=0
    casteCount: int=3
    buildDemolitionCost: Dict[Resource, int]
    combatRandomness: float = 0.5
    roadCost: Dict[Resource, int]={}
    roadPoints: int=10
    armyUpgradeCosts: Dict[int, Dict[Resource, int]]={}


class GameState(StateModel):
    teamStates: Dict[Team, TeamState]
    map: MapState
    world: WorldState

    def _setParent(self) -> None:
        for t in self.teamStates.values():
            t._setParent(self)
        self.map._setParent(self)

    def getArmy(self, id) -> Army:
        return self.teamStates[id.team].armies.get(id) if id != None else None

    @classmethod
    def createInitial(cls, entities: Entities) -> GameState:
        teamStates = {}
        for v in entities.teams.values():
            teamStates[v] = TeamState.createInitial(v, entities)

        return GameState(
            turn=0,
            teamStates={team: TeamState.createInitial(team, entities) for team in entities.teams.values()},
            map=MapState.createInitial(entities),
            world=WorldState(
                    buildDemolitionCost={entities["mge-obchod-3"]:10},
                    roadCost={entities["mge-stavivo-2"]:10,
                              entities["mge-nastroj-2"]:10,
                              entities.work:50},
                    armyUpgradeCosts={
                              2: {entities["mat-kladivo"]:2},
                              3: {entities["mat-kladivo"]:5, entities["mat-textil"]:3}}
            )
        )


    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._setParent()


    def normalize(self) -> None:
        for team in self.teamStates.values():
            team.resources = {r: a for r, a in team.resources.items() if a > 0}
            team.granary = {r: a for r, a in team.granary.items() if a > 0}
            team.storage = {r: a for r, a in team.storage.items() if a > 0}


def printResourceListForMarkdown(resources: Dict[Resource, Decimal], roundFunction = lambda x: x) -> str:
    message = MessageBuilder()
    with message.startList("") as addLine:
        for resource, amount in resources.items():
            addLine(f"[[{resource.id}|{roundFunction(amount)}]]")
    return message.message
