from pydantic import BaseModel
from game.actions.common import ActionFailedException
from game.actions.common import ActionCost, ActionCost, MessageBuilder
from game.entities import Entities, TeamEntity

from game.state import GameState, TeamId, TeamState

class ActionBase(BaseModel):
    class Config:
        # Action can have attributes that doesn't follow strict
        # type checking in via Pydantic - i.e., entities.
        arbitrary_types_allowed=True
  
    entities: Entities
    state: GameState

    errors: MessageBuilder = MessageBuilder()
    info: MessageBuilder = MessageBuilder()

    def cost(self) -> ActionCost:
        raise NotImplementedError("ActionBase is an interface")

    def commit(self) -> str:
        self.apply()
        if not self.errors.empty:
            raise ActionFailedException(self.errors)
        return self.info.message

    def apply(self) -> None:
        raise NotImplementedError("ActionBae is an interface")

    def delayedEffect(self) -> str:
        pass

class TeamActionBase(ActionBase):    
    @property
    def teamState(self) -> TeamState:
        return self.state.teamStates[self.args.teamEntity]

class TeamActionArgs(BaseModel):
    teamEntity: TeamEntity

