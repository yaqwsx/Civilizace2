from pydantic import BaseModel
from game.actions.actionBase import ActionBase
from game.actions.common import ActionCost

class ActionNextTurnArgs(BaseModel):
    pass

class ActionNextTurn(ActionBase):
    args: ActionNextTurnArgs

    def cost(self) -> ActionCost:
        return ActionCost([])

    def apply(self) -> str:
        currentTurn = self.state.turn
        self.state.turn += 1

        self.info.add("Začalo kolo " + (currentTurn+1))