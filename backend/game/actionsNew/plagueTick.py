from decimal import Decimal
from typing import Dict
from pydantic import BaseModel
from game.actions.actionBase import ActionArgs
from game.actionsNew.actionBaseNew import ActionBaseNew
from game.entities import Resource

class ActionPlagueTickArgs(ActionArgs):
    pass

class ActionPlagueTick(ActionBaseNew):
    args: ActionPlagueTickArgs


    def cost(self) -> Dict[Resource, Decimal]:
        return {}


    def _commitImpl(self) -> None:
        self._info += "Mor se rozšířil"
