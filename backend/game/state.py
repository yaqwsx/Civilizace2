from __future__ import annotations
from pydantic import BaseModel
from typing import List, Dict, Optional, Iterable, Union, Set
from decimal import Decimal

from game.entities import Entities, Tech

# Type Aliases
TeamId = str # intentionally left weak

class TeamState(BaseModel):
    redCounter: Decimal
    blueCounter: Decimal

    techs: Set[Tech]
    researching: Set[Tech] = set()

    @classmethod
    def createInitial(cls, teamId: TeamId, entities: Entities) -> TeamState:
        return TeamState(
            redCounter=0,
            blueCounter=0,
            techs=[entities["tec-start"]]
        )

class GameState(BaseModel):
    turn: int
    teamStates: Dict[TeamId, TeamState]

    @classmethod
    def createInitial(cls, teamIds: Iterable[TeamId], entities: Entities) -> GameState:
        return GameState(
            turn=0,
            teamStates={id: TeamState.createInitial(id, entities) for id in teamIds}
        )


