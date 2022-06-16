from __future__ import annotations

from decimal import Decimal
import math
from typing import Dict, Tuple
from game.actions.actionBase import ActionArgs, ActionResult
from game.actions.actionBase import ActionBase
from game.actions.common import ActionFailed
from game.entities import Resource, Team
from game.plague import getDeathToll, simulatePlague
from game.state import PlagueStats

class ActionPlagueFinishArgs(ActionArgs):
    team: Team

class ActionPlagueFinish(ActionBase):
    @property
    def args(self) -> ActionPlagueFinishArgs:
        assert isinstance(self._generalArgs, ActionPlagueFinishArgs)
        return self._generalArgs

    def cost(self) -> Dict[Resource, Decimal]:
        return {}

    def applyInitiate(self) -> ActionResult:
        tState = self.teamState
        if tState.plague is None:
            raise ActionFailed(f"Tým ještě nepodléhá morové ráně")

        return super().applyInitiate()

    @property
    def description(self):
        return f"Konec moru pro {self.args.team.name}"


    def _commitImpl(self) -> None:
        tState = self.teamState
        toll = getDeathToll(tState.plague, tState.population)
        currentPopulation = tState.resources.get(self.entities["res-obyvatel"], 0)
        tState.resources[self.entities["res-obyvatel"]] = max(0, currentPopulation - toll)


        tState.plague = None
        self._info.add("Mor byl ukončen.")
        self._info.add(f"Zemřelo {toll} obvyatel.")
        self._notifications[self.team] = ["Gratulujeme! Úspěšně jste porazili morovou epidemii."]

