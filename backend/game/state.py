from __future__ import annotations
from pydantic import BaseModel
from typing import List, Dict, Optional, Iterable, Union, Set
from decimal import Decimal
from game.entities import *


class MapTile(MapTileEntity): # Game state elemnent
    buildings: Dict[Building, Optional[TeamId]]={} # TeamId is stored for stats purposes only
    roadsTo: List[TeamId]=[]

    @property
    def features(self) -> List[TileFeature]:
        return self.naturalResources + self.buildings.keys()


class TeamState(BaseModel):
    team: Team
    redCounter: Decimal
    blueCounter: Decimal

    techs: Set[Tech]
    researching: Set[Tech] = set()

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

