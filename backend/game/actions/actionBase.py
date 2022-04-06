from pydantic import BaseModel
from game.actions.common import ActionCost, ActionCost, MessageBuilder
from game.entities import Entities

from game.state import GameState, TeamId


class ActionBase(BaseModel):
    teamId: TeamId
    entities: Entities
    state: GameState

    errors: MessageBuilder = MessageBuilder()
    info: MessageBuilder = MessageBuilder()

    def cost(self) -> ActionCost:
        raise NotImplementedError("ActionBase is an interface")

    def commit(self) -> str:
        self.apply()

    def apply(self) -> None:
        raise NotImplementedError("ActionBae is an interface")
