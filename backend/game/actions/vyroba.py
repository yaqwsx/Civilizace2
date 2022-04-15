from typing import List, Dict
from pydantic import BaseModel
from game.actions.actionBase import ActionBase, TeamActionBase
from game.actions.common import ActionArgumentException, ActionCost, ActionFailedException
from game.entities import Vyroba, ResourceBase, ResourceGeneric, Resource
from game.state import TeamId, TeamState

class ActionVyrobaArgs(BaseModel):
    vyroba: Vyroba
    count: int
    genericProductions: Dict[ResourceGeneric, Resource]

class ActionVyroba(TeamActionBase):
    args: ActionVyrobaArgs

    def cost(self) -> ActionCost:
        vyroba = self.args.vyroba
        cost = {item[0].id: item[1] for item in vyroba.cost.items()}
        return ActionCost(allowedDice = vyroba.die, requiredDots = vyroba.points, resources = vyroba.cost)

    def apply(self) -> None:
        self.info.add("Uspesne vyrobeno nic.")
