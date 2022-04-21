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

    def commit(self) -> ActionResult:
        # Reward was not given to the team yet. Assuming that happens outside action, same as with postponed()
        self.errors = MessageBuilder()
        self.info = MessageBuilder()
        cost = self.cost()
        
        self.commitInternal()
        if cost.postpone == 0:
            self.delayedInternal()
            
        if not self.errors.empty:
            return ActionResult(message=self.errors, reward=self.reward, succeeded=False)
        return ActionResult(message=self.info, reward=self.reward, succeeded=True)

    def commitInternal(self) -> None:
        raise NotImplementedError("ActionBae is an interface")

    def delayed(self) -> ActionResult:
        self.errors = MessageBuilder()
        self.info = MessageBuilder()
        self.delayedInternal()
        if not self.errors.empty:
            return ActionResult(message=self.errors, reward=self.reward, succeeded=False)
        return ActionResult(message=self.info, reward=self.reward, succeeded=True)

    def delayedInternal(self) -> None:
        pass

class TeamActionBase(ActionBase):    
    @property
    def teamState(self) -> TeamState:
        return self.state.teamStates[self.args.team]

class TeamActionArgs(BaseModel):
    team: Team

