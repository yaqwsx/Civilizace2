from decimal import Decimal
from math import ceil, floor
from typing import Dict, List, Optional, Set, Tuple
from game.actions.actionBase import ActionArgs
from game.actionsNew.ArmyDeploy import ActionArmyDeployArgs
from game.actionsNew.actionBaseNew import ActionBaseNew, ActionFailed, ActionResultNew
from game.entities import DieId, Resource, Vyroba
from game.state import MapTile, printResourceListForMarkdown

class ActionVyrobaArgs(ActionArgs):
    vyroba: Vyroba
    count: Decimal
    tile: MapTile
    plunder: bool
    army: Optional[ActionArmyDeployArgs]


class ActionVyroba(ActionBaseNew):

    @property
    def args(self) -> ActionVyrobaArgs:
        assert isinstance(self._generalArgs, ActionVyrobaArgs)
        return self._generalArgs


    def cost(self) -> Dict[Resource, Decimal]:
        return {resource: cost*self.args.count for resource, cost in self.args.vyroba.cost.items()}


    def diceRequirements(self) -> Tuple[Set[DieId], int]:
        points = (self.args.vyroba.points * (1 + self.args.count))
        return (self.teamState.getUnlockingDice(self.args.vyroba), ceil(points / 2))


    def _commitImpl(self) -> None:
        None


    def _applyDelayedReward(self) -> ActionResultNew:
        self._setupPrivateAttrs()
        reward = self.args.vyroba.reward
        resource = reward[0]
        amount = reward[1] * self.args.count

        multiplier = 1

        reward = {resource: amount*multiplier}

        tokens = self.teamState.receiveResources(reward)

        self._info += f"Tým obdržel [[{printResourceListForMarkdown(reward)}]]"
        if tokens != {}:
            self._info += f"Vydejte týmu [[{printResourceListForMarkdown(tokens, floor)}]]"

        return ActionResultNew(
            expected=True,
            message=self._info.message,
        )