from __future__ import annotations

from decimal import Decimal
import math
from typing import Dict, Tuple
from game.actions.actionBase import ActionArgs
from game.actions.actionBase import ActionBase
from game.entities import Resource
from game.plague import simulatePlague
from game.state import PlagueStats

class ActionPlagueTickArgs(ActionArgs):
    pass

class ActionPlagueTick(ActionBase):
    @property
    def args(self) -> ActionPlagueTickArgs:
        assert isinstance(self._generalArgs, ActionPlagueTickArgs)
        return self._generalArgs

    def cost(self) -> Dict[Resource, Decimal]:
        return {}

    @property
    def description(self):
        return "Morový tik"


    def _commitImpl(self) -> None:
        for tState in self.state.teamStates.values():
            if tState.plague is None:
                continue
            newStats, dead = simulatePlague(tState.plague, tState.population)
            currentPopulation = tState.resources.get(self.entities["res-obyvatel"], 0)
            tState.resources[self.entities["res-obyvatel"]] = max(0, currentPopulation - dead)
            tState.plague = newStats

