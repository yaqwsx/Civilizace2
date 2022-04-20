from typing import Dict
from collections import defaultdict
from decimal import Decimal
from pydantic import BaseModel
from game.actions.common import ActionCost, ActionCost, ActionException, MessageBuilder
from game.entities import Entities, Resource, Team

from game.state import GameState, TeamState

class ActionResult(BaseModel):
    message: MessageBuilder
    reward: Dict[Resource, Decimal]
    succeeded: bool

class ActionBase(BaseModel):
    class Config:
        # Action can have attributes that doesn't follow strict
        # type checking in via Pydantic - i.e., entities.
        arbitrary_types_allowed=True
  
    entities: Entities
    state: GameState

    errors: MessageBuilder = MessageBuilder()
    info: MessageBuilder = MessageBuilder()

    reward: Dict[Resource, int] = defaultdict(Decimal)

    def cost(self) -> ActionCost:
        return ActionCost()

    def commit(self) -> str:
        # Reward was not given to the team yet. Assuming that happens outside action, same as with postponed()
        self.commitInternal()
        if not self.errors.empty:
            raise ActionException(self.errors.message)
        return ActionResult(message=self.info, reward=self.reward, succeeded=True)

    def commitInternal(self) -> None:
        raise NotImplementedError("ActionBae is an interface")

    def delayed(self) -> ActionResult:
        pass

    def delayedInternal(self) -> str:
        pass

class TeamActionBase(ActionBase):    
    @property
    def teamState(self) -> TeamState:
        return self.state.teamStates[self.args.team]

class TeamActionArgs(BaseModel):
    team: Team

