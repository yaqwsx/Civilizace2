from __future__ import annotations

import enum
import inspect
import itertools
from decimal import Decimal
from typing import Any, Callable, Iterable, Mapping, Optional, Type, Union

from pydantic import BaseModel

from game.actions.common import MessageBuilder
from game.entities import (
    MAP_SIZE,
    TECHNOLOGY_START,
    TILE_DISTANCES_RELATIVE,
    TIME_PER_TILE_DISTANCE,
    Building,
    BuildingUpgrade,
    Entities,
    Entity,
    EntityId,
    EntityWithCost,
    MapTileEntity,
    Resource,
    TeamAttribute,
    TeamEntity,
    Tech,
    TileFeature,
    Vyroba,
)
from game.util import TModel


class StateModel(BaseModel):
    # By default, pydantic makes a copy of models on validation. We want to
    # avoid this as state is shared. Therefore, we override the behavior
    @classmethod
    def validate(cls: Type[TModel], value: Any) -> TModel:
        if isinstance(value, cls):
            return value  # This is the changed behavior
        return super().validate(value)

    # Workaround for using pydantic model with properties with setters
    def __setattr__(self, name: str, value: Any):
        try:
            super().__setattr__(name, value)
        except ValueError as e:
            setters = inspect.getmembers(
                self.__class__,
                predicate=lambda x: isinstance(x, property) and x.fset is not None,
            )
            for setter_name, func in setters:
                if setter_name == name:
                    object.__setattr__(self, name, value)
                    return
            raise e


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
    buildings: set[Building] = set()
    building_upgrades: set[BuildingUpgrade] = set()
    richnessTokens: int

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
    def features(self) -> list[TileFeature]:
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
    def inboundArmies(self) -> list[Army]:
        return []


class MapState(StateModel):
    size: int = MAP_SIZE
    tiles: dict[int, MapTile]
    armies: list[Army]

    def getTileById(self, id: str) -> Optional[MapTile]:
        tiles = [tile for tile in self.tiles.values() if tile.id == id]
        if len(tiles) != 1:
            return None
        return tiles[0]

    def getHomeOfTeam(self, team: TeamEntity) -> MapTile:
        home = self.getTileById(team.homeTile.id)
        assert home is not None, f"Team {team} has not home ({team.homeTile})"
        return home

    def _getRelativeIndex(self, team: TeamEntity, tile: MapTileEntity) -> int:
        home = self.getHomeOfTeam(team)
        relIndex = tile.index - home.index
        relIndexOffset = relIndex + self.size / 2
        return round((relIndexOffset % self.size) - self.size / 2)

    def getRawDistance(self, team: TeamEntity, tile: MapTileEntity) -> Decimal:
        relativeIndex = self._getRelativeIndex(team, tile)
        assert (
            relativeIndex in TILE_DISTANCES_RELATIVE
        ), "Tile {} is unreachable for {}".format(tile, team.id)
        return TILE_DISTANCES_RELATIVE[relativeIndex] * TIME_PER_TILE_DISTANCE

    def getActualDistance(
        self,
        team: TeamEntity,
        tile: MapTileEntity,
        teamStates: dict[TeamEntity, TeamState],
    ) -> Decimal:
        relativeIndex = self._getRelativeIndex(team, tile)
        assert (
            relativeIndex in TILE_DISTANCES_RELATIVE
        ), "Tile {} is unreachable for {}".format(tile, team.id)
        distance = TILE_DISTANCES_RELATIVE[relativeIndex] * TIME_PER_TILE_DISTANCE
        home = self.getHomeOfTeam(team)
        if relativeIndex != tile.index - home.index:
            distance *= Decimal(0.8)  # Tiles are around the map
        multiplier = Decimal(1)
        if self.getOccupyingTeam(tile, teamStates) == team:
            multiplier -= Decimal(0.5)
        return distance * multiplier

    def getReachableTiles(self, team: TeamEntity) -> list[MapTile]:
        index = self.getHomeOfTeam(team).index
        indexes = [(index + i) % self.size for i in TILE_DISTANCES_RELATIVE]
        return [self.tiles[i] for i in indexes]

    def getTeamArmies(self, team: TeamEntity) -> list[Army]:
        return [army for army in self.armies if army.team == team]

    def getOccupyingArmy(self, tile: MapTileEntity) -> Optional[Army]:
        for army in self.armies:
            if army.tile == tile and army.mode == ArmyMode.Occupying:
                return army
        return None

    def getOccupyingTeam(
        self, tile: MapTileEntity, teams: Iterable[TeamEntity]
    ) -> Optional[TeamEntity]:
        for army in self.armies:
            if army.tile == tile and army.mode == ArmyMode.Occupying:
                return army.team

        return next(filter(lambda team: team.homeTile == tile, teams), None)

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

    techs: set[Tech]
    researching: set[Tech] = set()
    attributes: set[TeamAttribute] = set()

    resources: dict[Resource, Decimal]
    granary: dict[Resource, int] = {}
    employees: dict[Vyroba, int] = {}
    population: Decimal

    def collectStickerEntitySet(self) -> set[Entity]:
        stickers = set()
        stickers.update(self._unlocked())
        return stickers

    def add_newborns(self, amount: int, entities: Entities) -> None:
        assert amount >= 0
        self.population += amount
        self.resources[entities.obyvatel] = (
            self.resources.get(entities.obyvatel, Decimal(0)) + amount
        )

    def kill_obyvatels(self, amount: int, entities: Entities) -> None:
        assert amount >= 0
        obyvatels = self.resources.get(entities.obyvatel, Decimal(0))
        real_amount = min(amount, obyvatels)
        self.population -= real_amount
        self.resources[entities.obyvatel] = obyvatels - real_amount

    @property
    def productions(self) -> Mapping[Resource, Decimal]:
        return {
            resource: amount
            for resource, amount in self.resources.items()
            if resource.isProduction
            if not resource.nontradable
        }

    @property
    def storage(self) -> Mapping[Resource, Decimal]:
        return {
            resource: amount
            for resource, amount in self.resources.items()
            if resource.isWithdrawable
        }

    def _unlocked(self) -> Iterable[EntityWithCost]:
        """Will return multiple copies, so it should be collected into a set/dict."""
        return itertools.chain(
            (e for group in self.team.groups for e in group.unlocks),
            (e for tech in self.techs for e in tech.unlocks),
        )

    def unlocked_techs(self) -> set[Tech]:
        return set(e for e in self._unlocked() if isinstance(e, Tech))

    def unlocked_vyrobas(self) -> set[Vyroba]:
        return set(e for e in self._unlocked() if isinstance(e, Vyroba))

    def unlocked_buildings(self) -> set[Building]:
        return set(e for e in self._unlocked() if isinstance(e, Building))

    def unlocked_attributes(self) -> set[TeamAttribute]:
        return set(e for e in self._unlocked() if isinstance(e, TeamAttribute))

    def unlocked_building_upgrades(self) -> set[BuildingUpgrade]:
        return set(e for e in self._unlocked() if isinstance(e, BuildingUpgrade))

    @staticmethod
    def create_initial(team: TeamEntity, entities: Entities) -> TeamState:
        return TeamState(
            team=team,
            techs=set([entities.techs[TECHNOLOGY_START]]),
            resources={
                entities.obyvatel: Decimal(100),
                entities.work: Decimal(100),
            },
            population=Decimal(100),
        )


class WorldState(StateModel):
    turn: int = 0
    casteCount: int = 3
    combatRandomness: Decimal = Decimal("0.5")
    roadCost: dict[Resource, int]
    roadPointsCost: int = 10
    armyUpgradeCosts: dict[int, dict[Resource, Decimal]] = {}  # TODO remove
    withdrawCapacity: int = 20

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
    teamStates: dict[TeamEntity, TeamState]
    map: MapState
    world: WorldState

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

    def normalize(self) -> None:
        for team in self.teamStates.values():
            assert all(amount >= 0 for amount in team.resources.values())
            assert all(amount >= 0 for amount in team.granary.values())
            assert all(amount >= 0 for amount in team.employees.values())
            team.resources = {
                res: amount for res, amount in team.resources.items() if amount > 0
            }
            team.granary = {
                res: amount for res, amount in team.granary.items() if amount > 0
            }
            team.employees = {
                emp: amount for emp, amount in team.employees.items() if amount > 0
            }
