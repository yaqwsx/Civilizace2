from typing import Dict
from game.actions.actionBase import TeamActionBase, ActionArgs
from game.actions.common import ActionCost
from game.entities import Vyroba, Resource, Resource

class ActionVyrobaArgs(ActionArgs):
    vyroba: Vyroba
    count: int
    genericProductions: Dict[Resource, Resource]

class ActionVyroba(TeamActionBase):
    args: ActionVyrobaArgs

    def cost(self) -> ActionCost:
        vyroba = self.args.vyroba
        cost = {item[0].id: item[1]*self.args.count for item in vyroba.cost.items()}
        return ActionCost(allowedDice = vyroba.die, requiredDots = vyroba.points, resources = vyroba.cost)

    def commitInternal(self) -> None:
        self.info.add("Uspesne vyrobeno nic.")
