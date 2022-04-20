from pydantic import BaseModel
from game.actions.actionBase import ActionBase
from game.actions.common import ActionCost

class ActionNextTurnArgs(BaseModel):
    pass

class ActionNextTurn(ActionBase):
    args: ActionNextTurnArgs

    def cost(self) -> ActionCost:
        return ActionCost(resources={})

    def commitInternal(self) -> None:
        self.state.turn += 1
        self.info.add("Začalo kolo {}".format(self.state.turn))
