from decimal import Decimal
from typing import Dict, List, Optional, Set, Tuple
from game.actions.actionBase import ActionArgs
from game.actions.common import ActionFailed
from game.actionsNew.actionBaseNew import ActionBaseNew
from game.entities import DieId, Resource, Tech, Team

class ActionResearchArgsNew(ActionArgs):
    tech: Tech
    task: Optional[str]=None

class ActionResearchStartNew(ActionBaseNew):

    @property
    def args(self) -> ActionResearchArgsNew:
        assert isinstance(self._generalArgs, ActionResearchArgsNew)
        return self._generalArgs


    def cost(self) -> Dict[Resource, Decimal]:
        dice = self.teamState.getUnlockingDice(self.args.tech)
        if len(dice) == 0:
            raise ActionFailed(f"Zkoumání technologie [[{self.args.tech.id}]] ještě není odemčeno")
        return self.args.tech.cost


    def diceRequirements(self) -> Tuple[Set[DieId], int]:
        return (self.teamState.getUnlockingDice(self.args.tech), self.args.tech.points)


    def _commitImpl(self) -> None:
        if self.args.tech in self.teamState.techs:
            raise ActionFailed(f"Technologie [[{self.args.tech.id}]] je již vyzkoumána")

        if self.args.tech in self.teamState.researching:
            raise ActionFailed(f"Výzkum technologie [[{self.args.tech.id}]] již probíhá")

        if not self.args.task:
            self._warnings += "**Pozor:** k výzkumu nebyl vybrán úkol."
        else:
            self._info += f"Zadejte týmu úkol {self.args.task}"

        self.teamState.researching.add(self.args.tech)
        self._info += "Výzkum technologie [[" + self.args.tech.id + "]] začal."
