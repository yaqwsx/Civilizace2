from __future__ import annotations
import enum
from pydantic import BaseModel, PrivateAttr
from typing import Any, Callable, List, Dict, Mapping, Optional, Type, TypeVar, Set
from decimal import Decimal
from game.actions.common import MessageBuilder
from game.entities import *
from game.util import get_by_entity_id

TModel = TypeVar("TModel", bound="BaseModel")


class StateModel(BaseModel):
    _parent: Optional[StateModel] = PrivateAttr()

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
    def validate(cls: Type[TModel], value: Any) -> TModel:
        if isinstance(value, cls):
            return value  # This is the changed behavior
        return super().validate(value)

    def _setParent(self, parent: Optional[StateModel] = None):
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
    team: TeamEntity  # duplicates: items in TeamEntity.armies
    index: int
    name: str
    level: int
    equipment: int = 0  # number of weapons the army currently carries
    boost: int = -1  # boost added by die throw
    tile: Optional[MapTileEntity] = None
    mode: ArmyMode = ArmyMode.Idle
    goal: Optional[ArmyGoal] = None

    @property
    def parent(self) -> MapState:
        assert isinstance(self._parent, MapState)
        return self._parent

    @property
    def capacity(self) -> int:
        return 5 + 5 * self.level

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


class MapTile(StateModel):  # Game state element
    entity: MapTileEntity
    buildings: Set[Building] = set()
    building_upgrades: Set[BuildingUpgrade] = set()
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
    def richness(self) -> int:
        return self.entity.richness

    @property
    def features(self) -> List[TileFeature]:
        return (
            self.entity.naturalResources
            + list[TileFeature](self.buildings)
            + list(self.building_upgrades)
        )

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
    size: int = MAP_SIZE
    tiles: Dict[int, MapTile]
    armies: List[Army]

    def _setParent(self, parent: Optional[StateModel] = None):
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

    def getHomeOfTeam(self, team: TeamEntity) -> MapTile:
        return self.parent.teamStates[team].homeTile

    def _getRelativeIndex(self, team: TeamEntity, tile: MapTileEntity) -> int:
        home = self.getHomeOfTeam(team)
        assert home != None, "Team {} has no home tile".format(team.id)
        relIndex = tile.index - home.index
        relIndexOffset = relIndex + self.size / 2
        return round((relIndexOffset % self.size) - self.size / 2)

    def getRawDistance(self, team: TeamEntity, tile: MapTileEntity) -> Decimal:
        relativeIndex = self._getRelativeIndex(team, tile)
        assert (
            relativeIndex in TILE_DISTANCES_RELATIVE
        ), "Tile {} is unreachable for {}".format(tile, team.id)
        return TILE_DISTANCES_RELATIVE[relativeIndex] * TIME_PER_TILE_DISTANCE

    def getActualDistance(self, team: TeamEntity, tile: MapTileEntity) -> Decimal:
        relativeIndex = self._getRelativeIndex(team, tile)
        assert (
            relativeIndex in TILE_DISTANCES_RELATIVE
        ), "Tile {} is unreachable for {}".format(tile, team.id)
        distance = TILE_DISTANCES_RELATIVE[relativeIndex] * TIME_PER_TILE_DISTANCE
        home = self.getHomeOfTeam(team)
        if relativeIndex != tile.index - home.index:
            distance *= Decimal(0.8)  # Tiles are around the map
        multiplier = Decimal(1)
        teamState = self.parent.teamStates[team]
        if tile in teamState.roadsTo:
            multiplier -= Decimal(0.5)
        if self.getOccupyingTeam(tile) == team:
            multiplier -= Decimal(0.5)
        return distance * multiplier

    def getReachableTiles(self, team: TeamEntity) -> List[MapTile]:
        index = self.getHomeOfTeam(team).index
        indexes = [(index + i) % self.size for i in TILE_DISTANCES_RELATIVE]
        return [self.tiles[i] for i in indexes]

    def getTeamArmies(self, team: TeamEntity) -> List[Army]:
        return [army for army in self.armies if army.team == team]

    def getOccupyingArmy(self, tile: MapTileEntity) -> Optional[Army]:
        for army in self.armies:
            if army.tile == tile and army.mode == ArmyMode.Occupying:
                return army
        return None

    def getOccupyingTeam(self, tile: MapTileEntity) -> Optional[TeamEntity]:
        for army in self.armies:
            if army.tile == tile and army.mode == ArmyMode.Occupying:
                return army.team

        for team in self.parent.teamStates.keys():
            if team.homeTile == tile:
                return team
        return None

    def retreatArmy(self, army: Army) -> int:
        result = army.equipment
        assert army.tile is not None
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

    @staticmethod
    def create_initial(entities: Entities) -> MapState:
        armies = []
        teams = entities.teams.values()
        armies.extend(
            Army(team=team, index=i, name="A", level=3) for i, team in enumerate(teams)
        )
        armies.extend(
            Army(team=team, index=i + 8, name="B", level=2)
            for i, team in enumerate(teams)
        )
        armies.extend(
            Army(team=team, index=i + 16, name="C", level=1)
            for i, team in enumerate(teams)
        )

        return MapState(
            tiles={
                tile.index: MapTile(entity=tile, richnessTokens=tile.richness)
                for tile in entities.tiles.values()
            },
            armies=armies,
        )


class TeamState(StateModel):
    team: TeamEntity
    redCounter: Decimal = Decimal(0)
    blueCounter: Decimal = Decimal(0)

    turn: int = 0
    throwCost: int = 10

    techs: Set[Tech]
    researching: Set[Tech] = set()
    attributes: Set[TeamAttribute] = set()

    roadsTo: Set[MapTileEntity] = set()

    resources: Dict[Resource, Decimal]
    storage: Dict[Resource, Decimal]
    granary: Dict[Resource, Decimal] = {}
    storageCapacity: Decimal = Decimal(10)
    employees: Decimal = Decimal(0)

    discoveredTiles: Set[MapTileEntity] = set()

    def _setParent(self, parent: Optional[StateModel] = None):
        self._parent = parent

    @property
    def parent(self) -> GameState:
        assert isinstance(self._parent, GameState)
        return self._parent

    @property
    def homeTile(self) -> MapTile:
        tile = self.parent.map.getTileById(self.team.homeTile.id)
        assert tile is not None
        return tile

    def collectStickerEntitySet(self) -> set[Entity]:
        stickers = set()
        stickers.update(self.techs)
        stickers.update(self.vyrobas)
        stickers.update(self.buildings)
        return stickers

    def addEmployees(self, amount: int) -> None:
        self.employees += amount

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
            buildings.update(t.unlocksBuildings)
        return buildings

    @property
    def unlocked_attributes(self) -> set[TeamAttribute]:
        attributes = set()
        for tech in self.techs:
            attributes.update(tech.unlocksTeamAttributes)
        return attributes


    @property
    def work(self) -> Decimal:
        return get_by_entity_id(RESOURCE_WORK, self.resources, Decimal(0))

    @property
    def obyvatels(self) -> Decimal:
        return get_by_entity_id(RESOURCE_VILLAGER, self.resources, Decimal(0))

    @property
    def population(self) -> Decimal:
        return self.obyvatels + self.employees

    @property
    def culture(self) -> Decimal:
        return get_by_entity_id(RESOURCE_CULTURE, self.resources, Decimal(0))

    @staticmethod
    def create_initial(team: TeamEntity, entities: Entities) -> TeamState:
        return TeamState(
            team=team,
            techs=set([entities.techs[TECHNOLOGY_START]]),
            resources={
                entities.obyvatel: Decimal(100),
                entities.work: Decimal(100),
            },
            storage={},
        )


class WorldState(StateModel):
    turn: int = 0
    casteCount: int = 3
    combatRandomness: Decimal = Decimal("0.5")
    roadCost: Dict[Resource, int]
    roadPointsCost: int = 10
    armyUpgradeCosts: Dict[int, Dict[Resource, Decimal]] = {}  # TODO remove

    @staticmethod
    def create_initial(entities: Entities) -> WorldState:
        return WorldState(
            roadCost={
                entities.work: 50,
                entities.resources["mge-stavivo"]: 10,
                entities.resources["mge-nastroj"]: 10,
            },
            roadPointsCost=10,
        )


class GameState(StateModel):
    teamStates: Dict[TeamEntity, TeamState]
    map: MapState
    world: WorldState

    def _setParent(self) -> None:
        for t in self.teamStates.values():
            t._setParent(self)
        self.map._setParent(self)

    @staticmethod
    def create_initial(entities: Entities) -> GameState:
        return GameState(
            teamStates={
                team: TeamState.create_initial(team, entities)
                for team in entities.teams.values()
            },
            map=MapState.create_initial(entities),
            world=WorldState.create_initial(entities),
        )

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._setParent()

    def normalize(self) -> None:
        for team in self.teamStates.values():
            assert all(amount >= 0 for amount in team.resources.values())
            assert all(amount >= 0 for amount in team.granary.values())
            assert all(amount >= 0 for amount in team.storage.values())
            team.resources = {
                res: amount for res, amount in team.resources.items() if amount > 0
            }
            team.granary = {
                res: amount for res, amount in team.granary.items() if amount > 0
            }
            team.storage = {
                res: amount for res, amount in team.storage.items() if amount > 0
            }


def printResourceListForMarkdown(
    resources: Mapping[Resource, Union[Decimal, int]],
    roundFunction: Callable[[Decimal], Any] = lambda x: x,
) -> str:
    message = MessageBuilder()
    with message.startList() as addLine:
        for resource, amount in resources.items():
            addLine(f"[[{resource.id}|{roundFunction(Decimal(amount))}]]")
    return message.message
