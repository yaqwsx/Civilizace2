from __future__ import annotations
from math import floor
from pydantic import BaseModel
from typing import ClassVar, List, Dict, Optional, Iterable, Union, Set
from decimal import Decimal
from game.entities import *


STARTER_ARMY_PRESTIGES = [15,20,25]
TILE_DISTANCES_RELATIVE = {0: Decimal(0),
    -9: Decimal(1.5), -3: Decimal(1.5), 2: Decimal(1.5), 7: Decimal(1.5), 9: Decimal(1.5),
    -2: Decimal(1), -1: Decimal(1), 1: Decimal(1), 5: Decimal(1), 6: Decimal(1)}


class Army(BaseModel):
    team: Team # duplicates: items in Team.armies
    prestige: int
    equipment: int=0 # number of weapons the army currently carries
    boost: int=0 # boost added by die throw
    tile: Optional[MapTile]=None
    
    @property
    def strength(self):
        return self.strength + self.boost + 5

    @property
    def isMarching(self):
        return self.tile == None


class MapTile(BaseModel): # Game state elemnent
    entity: MapTileEntity
    occupiedBy: Optional[Army]=None
    buildings: Dict[Building, Optional[TeamId]]={} # TeamId is stored for stats purposes only

    @property
    def features(self) -> List[TileFeature]:
        return self.naturalResources + self.buildings.keys()


class HomeTile(MapTile):
    team: Team
    roadsTo: List[MapTile]=[]

    @classmethod
    def createInitial(cls, team: Team, tile: MapTileEntity, entities: Entities) -> HomeTile:
        return HomeTile(name="Domovské pole " + team.name,
                       index=tile.index,
                       parcelCount=3,
                       richness=0,
                       naturalResources = tile.naturalResources)


class MapState(BaseModel):
    wildTiles: Dict[int, MapTile]
    homeTiles: Dict[Team, HomeTile]

    def getRawDistance(self, team: TeamState, tile: MapTile) -> Decimal:
        assert team.homeTile.index >= 0
        teamTile = team.homeTile.index - tile.index
        return 0

    def getTile(self, index:int) -> MapTile:
        return self.wildTiles[index]


    def getHomeTile(self, team: Team) -> MapTile:
        return self.homeTiles[team]


    @property
    def tiles(self):
        # TODO: how to cache this?
        return list(self.wildTiles.values()) + list(self.homeTiles.values())


    @classmethod
    def createInitial(cls, entities: Entities) -> MapState:
        return MapState(
            wildTiles = {tile.index: MapTile(entity=tile) for tile in entities.tiles.values() if tile.index % 4 != 1},
            homeTiles = {}
        )


class TeamState(BaseModel):
    team: Team
    redCounter: Decimal
    blueCounter: Decimal

    techs: Set[Tech]
    researching: Set[Tech] = set()
    armies: List[Army]

    @classmethod
    def createInitial(cls, team: Team, entities: Entities) -> TeamState:
        armies = [Army(team=team, prestige=x) for x in STARTER_ARMY_PRESTIGES]
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

