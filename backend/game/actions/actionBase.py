from pydantic import BaseModel
from backend.game.actions.common import ActionException
from game.actions.common import ActionCost, ActionCost, MessageBuilder
from game.entities import Entities

from game.state import GameState, TeamId


class ActionBase(BaseModel):
    entities: Entities
    state: GameState

    errors: MessageBuilder = MessageBuilder()
    info: MessageBuilder = MessageBuilder()

    def cost(self) -> ActionCost:
        raise NotImplementedError("ActionBase is an interface")

    def commit(self) -> str:
        self.apply()
        if not self.errors.empty:
            raise ActionException(self.errors)
        return self.info.message

    def apply(self) -> None:
        raise NotImplementedError("ActionBae is an interface")

    def delayedEffect(self) -> str:
        pass
