from __future__ import annotations

from decimal import Decimal
import math
from typing import Dict, Tuple
from game.actions.actionBase import ActionArgs, ActionResult
from game.actions.actionBase import ActionBase
from game.actions.common import ActionFailed
from game.entities import Resource, Team
from game.plague import simulatePlague
from game.state import PlagueStats

class ActionPlagueStartArgs(ActionArgs):
    team: Team

class ActionPlagueStart(ActionBase):
    @property
    def args(self) -> ActionPlagueStartArgs:
        assert isinstance(self._generalArgs, ActionPlagueStartArgs)
        return self._generalArgs

    def cost(self) -> Dict[Resource, Decimal]:
        return {}

    def applyInitiate(self) -> ActionResult:
        tState = self.teamState
        if tState.plague is not None:
            raise ActionFailed(f"Tým už podléhá Morové ráně")

        return super().applyInitiate()

    @property
    def description(self):
        return f"Začátek moru pro {self.args.team.name}"


    def _commitImpl(self) -> None:
        tState = self.teamState
        tState.plague = PlagueStats()
        self._info.add("Mor byl započat.")
        self._notifications[self.team] = ["Váš národ byl napaden morovou epidemií. Musíte ji vyřešit. Do té doby nejsou k dipozici žádné herní akce"]
