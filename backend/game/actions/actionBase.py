from typing import Dict, Optional
from collections import defaultdict
from decimal import Decimal
from pydantic import BaseModel
from game.actions.common import ActionCost, ActionCost, ActionException, ActionResult, CancelationResult, InitiateResult, MessageBuilder
from game.entities import Entities, Resource, Team

from game.state import GameState, TeamState, printResourceListForMarkdown

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

    def initiate(self, cost: Optional[ActionCost]) -> InitiateResult:
        if self.args.team is not None:
            raise ActionException("Akce má specifikovaný tým, ale nestrhává mu zdroje")
        return InitiateResult()

    def commit(self, cost: Optional[ActionCost]=None) -> ActionResult:
        # Reward was not given to the team yet. Assuming that happens outside action, same as with postponed()
        self.errors = MessageBuilder()
        self.info = MessageBuilder()

        if cost is None:
            cost = self.cost()

        self.info.add(self.commitInternal())
        if cost.postpone == 0:
            self.info.add(self.delayedInternal())

        if not self.errors.empty:
            return ActionResult(message=self.errors.message, reward=self.reward, succeeded=False)
        return ActionResult(message=self.info.message, reward=self.reward, succeeded=True)

    def abandon(self, cost: Optional[ActionCost]) -> CancelationResult:
        raise NotImplementedError("ActionBase is an interface")

    def cancel(self, cost: Optional[ActionCost]) -> CancelationResult:
        raise NotImplementedError("ActionBase is an interface")

    def commitInternal(self) -> str:
        raise NotImplementedError("ActionBase is an interface")

    def delayed(self) -> ActionResult:
        self.errors = MessageBuilder()
        self.info = MessageBuilder()
        self.info.add(self.delayedInternal())
        if not self.errors.empty:
            return ActionResult(message=self.errors.message, reward=self.reward, succeeded=False)
        return ActionResult(message=self.info.message, reward=self.reward, succeeded=True)

    def delayedInternal(self) -> str:
        pass

    def payWork(self, amount: int) -> bool:
        """
        Try to pay work, return if we succeeded
        """
        if amount != 0:
            raise ActionException("Chce se zaplatit práce na akci, která není týmová")
        return True

    def commitReward(self, r: Dict[Resource, Decimal]) -> None:
        """
        Award resources for the action
        """
        if len(r) != 0:
            raise ActionException("Chce se odměňovat na akci, která není týmová")


class TeamActionBase(ActionBase):
    @property
    def teamState(self) -> TeamState:
        return self.state.teamStates[self.args.team]

    @property
    def team(self) -> Team:
        return self.args.team


    def initiate(self, cost: Optional[ActionCost]) -> InitiateResult:
        if self.team is None or cost is None:
            return InitiateResult()
        result = InitiateResult()
        tState = self.state.teamStates[self.team]
        productions = {r: a for r, a in cost.resources.items() if r.isProduction}
        for r, required in productions:
            available = tState.resources.get(r, 0)
            if available < required:
                result.missingProductions[r, required - available]
        if not result.succeeded:
            return result
        for r, required in productions:
            tState.resources[r] -= required
        result.materials = {r: a for r, a in cost.resources.items() if r.isTracked}
        return result

    def abandon(self, cost: Optional[ActionCost]) -> CancelationResult:
        if self.team is None or cost is None:
            return CancelationResult()
        tState = self.state.teamStates[self.team]
        productions = {r: a for r, a in cost.resources.items() if r.isProduction}
        for r, required in productions:
            tState.resources[r] += required
        return CancelationResult()

    def cancel(self, cost: Optional[ActionCost]) -> CancelationResult:
        if self.team is None or cost is None:
            return CancelationResult()
        result = self.abandon(cost)
        result.materials = {r: a for r, a in cost.resources.items() if r.isTracked}
        return result

    def payWork(self, amount: int) -> bool:
        currentWork = self.teamState.resources.get(self.entities.work, 0)
        if currentWork - amount < 0:
            self.teamState.resources[self.entities.work] = 0
            return False
        self.teamState.resources[self.entities.work] = currentWork - amount
        return True

    def commitReward(self, rew: Dict[Resource, Decimal]) -> None:
        for r, a in rew.items():
            if not r.isProduction:
                raise ActionException("Je chtěno se odměnit něčím, co není produkce. Řekni to Maarovi")
            self.teamState.resources[r] = self.teamState.resources.get(r, 0) + a


class ActionArgs(BaseModel):
    team: Optional[Team]

