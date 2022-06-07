from decimal import Decimal
from typing import Dict
from pydantic import BaseModel
from game.actions.actionBase import ActionArgs
from game.actions.actionBase import ActionBase
from game.entities import Resource

class ActionNextTurnArgs(ActionArgs):
    pass

class ActionNextTurn(ActionBase):
    args: ActionNextTurnArgs

    @property
    def args(self) -> ActionNextTurnArgs:
        assert isinstance(self._generalArgs, ActionNextTurnArgs)
        return self._generalArgs


    def cost(self) -> Dict[Resource, Decimal]:
        return {}


    def _commitImpl(self) -> None:
        self.state.turn += 1
        self._info += f"Začalo kolo {self.state.turn}"
