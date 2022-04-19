from __future__ import annotations
from cmath import nan
import enum
from math import floor
from pydantic import BaseModel
from typing import ClassVar, List, Dict, Optional, Iterable, Union, Set
from decimal import Decimal
from game.entities import *

class ArmyState(enum.Enum):
    Idle = 0
    Marching = 1
    Occupying = 2

class ArmyId(BaseModel):
    prestige: int
    team: Team

    def __hash__(self):
        return self.team.__hash__() + self.prestige

    def __eq__(self, other):
        if type(other) != type(self):
            return False
        return self.team == other.team and self.id == other.id

class Army(BaseModel):
    team: Team # duplicates: items in Team.armies
    prestige: int
    equipment: int=0 # number of weapons the army currently carries
    boost: int=0 # boost added by die throw
    tile: Optional[MapTileEntity]=None
    state: ArmyState=ArmyState.Idle

    @property 
    def capacity(self) -> int:
        return self.prestige - BASE_ARMY_STRENGTH

    @property
    def id(self) -> ArmyId:
        return ArmyId(self.prestige, self.team)

    @property
    def strength(self) -> int:
        return self.equipment + self.boost + BASE_ARMY_STRENGTH

    @property
    def isMarching(self) -> bool:
        return self.tile == None

    def retreat(self) -> int:
        result = self.equipment
        self.state = ArmyState.Idle
        self.equipment = 0
        self.boost = 0
        self.tile = None
        return result

    def occupy(self, tile: MapTile):
        self.state = ArmyState.Occupying
        self.boost = 0
        self.tile = tile.entity
        tile.occupiedBy = self.id


class MapTile(BaseModel): # Game state elemnent
    entity: MapTileEntity
    occupiedBy: Optional[Tuple[int, Team]]=None
    buildings: Dict[Building, Optional[TeamId]]={} # TeamId is stored for stats purposes only

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
        return self.naturalResources + self.buildings.keys()


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


class MapState(BaseModel):
    size: int=MAP_SIZE
    tiles: Dict[int, MapTile]
    homeTiles: Dict[Team, HomeTile]

    def _getRelativeIndex(self, team: Team, tile: MapTile) -> int:
        home = self.homeTiles[team]
        assert home != None, "Team {} has no home tile".format(team.id)
        relIndex = tile.index - home.index
        relIndexOffset = relIndex + self.size/2
        return (relIndexOffset % self.size) - self.size/2

    def getRawDistance(self, team: Team, tile: MapTile) -> Decimal:
        relativeIndex = self._getRelativeIndex(team, tile)
        assert relativeIndex in TILE_DISTANCES_RELATIVE, "Tile {} is unreachable for {}".format(tile, team.id)
        return TILE_DISTANCES_RELATIVE[relativeIndex] * TIME_PER_TILE_DISTANCE

    def getActualDistance(self, team: Team, tile: MapTile) -> Decimal:
        relativeIndex = self._getRelativeIndex(team, tile)
        assert relativeIndex in TILE_DISTANCES_RELATIVE, "Tile {} is unreachable for {}".format(tile, team.id)
        distance = TILE_DISTANCES_RELATIVE[relativeIndex] * TIME_PER_TILE_DISTANCE
        home = self.homeTiles[team]
        if relativeIndex != tile.index - home.index:
            distance *= Decimal(0.8) # Tiles are around the map
        multiplier = 1
        if tile.entity in home.roadsTo:
            multiplier -= 0.5
        if tile.occupiedBy != None and tile.occupiedBy.team == team:
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


class TeamState(BaseModel):
    team: Team
    redCounter: Decimal
    blueCounter: Decimal

    techs: Set[Tech]
    researching: Set[Tech] = set()
    armies: Dict[ArmyId, Army]

    @classmethod
    def createInitial(cls, team: Team, entities: Entities) -> TeamState:
        armies = {ArmyId(prestige=x, team=team): Army(team=team, prestige=x) for x in STARTER_ARMY_PRESTIGES}
        return TeamState(
            team=team,
            redCounter=0,
            blueCounter=0,
            techs=[entities["tec-start"]],
            armies=armies,
        )


class GameState(BaseModel):
    turn: int
    teamStates: Dict[Team, TeamState]
    map: MapState

    def getArmy(self, id: ArmyId) -> Army:
        return self.teamStates[id.team].armies[id]

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

