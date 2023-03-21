from decimal import Decimal
from typing import Dict, Iterable, List, Optional, Set, Tuple
from game.actions.actionBase import ActionArgs, ActionBase
from game.actions.common import ActionFailed
from game.entities import Die, Resource, Tech, Team

class ActionResearchArgs(ActionArgs):
    team: Team
    tech: Tech
    task: Optional[str]=None

class ActionResearchStart(ActionBase):

    @property
    def args(self) -> ActionResearchArgs:
        assert isinstance(self._generalArgs, ActionResearchArgs)
        return self._generalArgs

    @property
    def description(self):
        return f"Výzkum technologie {self.args.tech.name} ({self.args.team.name})"


    def cost(self) -> Dict[Resource, Decimal]:
        assert self.teamState is not None
        if any(True for _ in self.teamState.getUnlockingDice(self.args.tech)):
            raise ActionFailed(f"Zkoumání technologie [[{self.args.tech.id}]] ještě není odemčeno")
        return self.args.tech.cost


    def diceRequirements(self) -> Tuple[Iterable[Die], int]:
        assert self.teamState is not None
        return (self.teamState.getUnlockingDice(self.args.tech), self.args.tech.points)


    def _commitImpl(self) -> None:
        assert self.teamState is not None
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
