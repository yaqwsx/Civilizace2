from __future__ import annotations
from pydantic import BaseModel
from typing import List, Dict, Optional, Iterable, Union
from decimal import Decimal

# Type Aliases
TeamId = str # intentionally left weak

class TeamState(BaseModel):
    redCounter: Decimal
    blueCounter: Decimal

    @classmethod
    def createInitial(cls, teamId: TeamId) -> TeamState:
        return TeamState(
            redCounter=0,
            blueCounter=0
        )


class GameState(BaseModel):
    round: int
    teamStates: Dict[TeamId, TeamState]

    @classmethod
    def createInitial(cls, teamIds: Iterable[TeamId]) -> GameState:
        return GameState(
            round=0,
            teamStates={id: TeamState.createInitial(id) for id in teamIds}
        )


