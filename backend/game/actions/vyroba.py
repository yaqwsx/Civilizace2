from decimal import Decimal
from math import ceil, floor
from typing import Dict, List, Optional, Set, Tuple
from game.actions.actionBase import ActionArgs
from game.actions.actionBase import ActionBase
from game.entities import DieId, MapTileEntity, Resource, Team, Vyroba
from game.state import ArmyGoal, printResourceListForMarkdown

class ActionVyrobaArgs(ActionArgs):
    team: Team
    vyroba: Vyroba
    count: Decimal
    tile: MapTileEntity
    plunder: bool
    genericsMapping: Dict[Resource, Resource]={}

    armyIndex: Optional[int]
    goal: Optional[ArmyGoal]
    equipment: Optional[int]


class ActionVyroba(ActionBase):

    @property
    def args(self) -> ActionVyrobaArgs:
        assert isinstance(self._generalArgs, ActionVyrobaArgs)
        return self._generalArgs

    @property
    def description(self):
        return f"Výroba [[{self.args.vyroba.reward[0]}|{self.args.vyroba.reward[1]*self.args.count}]] ({self.args.team.name})"


    def cost(self) -> Dict[Resource, Decimal]:
        return {resource: cost*self.args.count for resource, cost in self.args.vyroba.cost.items()}


    def diceRequirements(self) -> Tuple[Set[DieId], int]:
        points = (self.args.vyroba.points * (1 + self.args.count))
        return (self.teamState.getUnlockingDice(self.args.vyroba), ceil(points / 2))


    def requiresDelayedEffect(self) -> int:
        return self.state.map.getActualDistance(self.args.team, self.args.tile)


    def _commitImpl(self) -> None:
        self._info += f"Zadání výroby bylo úspěšné. Akce se vyhodnotí za {ceil(self.requiresDelayedEffect() / 60)} minut"


    def _applyDelayedReward(self) -> None:
        self._setupPrivateAttrs()
        reward = self.args.vyroba.reward
        resource = reward[0]
        amount = reward[1] * self.args.count

        multiplier = 1

        reward = {resource: amount*multiplier}

        tokens = self.receiveResources(reward, instantWithdraw=True)

        self._info += f"Tým obdržel {printResourceListForMarkdown(reward)}"
        if tokens != {}:
            self._info += f"Vydejte týmu {printResourceListForMarkdown(tokens, floor)}"
