from __future__ import annotations
from pydantic import BaseModel
from typing import List, Dict, Optional, Iterable, Union, Set
from decimal import Decimal
from game.entities import *


class Army(BaseModel):
    team: Team # duplicates: items in Team.armies
    prestige: int
    equipment: int # number of weapons the army carries
    boost: int # boost added by die throw
    tile: Optional[MapTile]
    
    @property
    def strength(self):
        return self.strength + self.boost + 5

    @property
    def isMarching(self):
        return self.tile == None


class MapTile(BaseModel): # Game state elemnent
    name: str
    index: int
    parcelCount: int
    naturalResources: List[NaturalResource]
    richness: int=0
    occupiedBy: Optional[Army]
    buildings: Dict[Building, Optional[TeamId]]={} # TeamId is stored for stats purposes only

    @property
    def features(self) -> List[TileFeature]:
        return self.naturalResources + self.buildings.keys()

    @classmethod
    def createInitial(cls, tile: MapTileEntity) -> MapTile:
        return MapTile(name=tile.name,
                       index=tile.index,
                       parcelCount=tile.parcelCount,
                       richness=tile.richness,
                       naturalResources = List(tile.naturalResources))



class HomeTile(MapTile):
    teamEntity: Team
    roadsTo: List[MapTile]=[]

    @classmethod
    def createInitial(cls, team: Team, entities: Entities) -> HomeTile:
        return HomeTile(name="Domovské pole " + team.name,
                       index=-1,
                       parcelCount=3,
                       richness=0,
                       naturalResources = entities["nat-voda"])


class MapState(BaseModel):
    wildTiles: Dict[int, MapTile]
    homeTiles: List[HomeTile]

    @property
    def tiles(self):
        # TODO: how to cache this?
        return self.wildTiles.values() + self.homeTiles 


    @classmethod
    def createInitial(cls, entities: Entities) -> MapState:
        wildTiles = {tile.index: MapTile.createInitial(tile) for tile in entities.tiles}
        homeTiles = []
        return TeamState(
            wildTiles=wildTiles,
            homeTiles=homeTiles
        )


class TeamState(BaseModel):
    team: Team
    redCounter: Decimal
    blueCounter: Decimal

    techs: Set[Tech]
    researching: Set[Tech] = set()
    armies: Set[Army]

    @classmethod
    def createInitial(cls, team: Team, entities: Entities) -> TeamState:
        return TeamState(
            team=team,
            redCounter=0,
            blueCounter=0,
            techs=[entities["tec-start"]]
        )


class GameState(BaseModel):
    turn: int
    teamStates: Dict[Team, TeamState]

    @classmethod
    def createInitial(cls, entities: Entities) -> GameState:
        teamStates = {}
        for v in entities.teams.values():
            teamStates[v] = TeamState.createInitial(v, entities)

        return GameState(
            turn=0,
            teamStates={team: TeamState.createInitial(team, entities) for team in entities.teams.values()}
        )

