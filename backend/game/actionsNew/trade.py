from decimal import Decimal
from math import ceil
from typing import Dict, List, Optional, Set, Tuple
from game.actions.actionBase import ActionArgs
from game.actions.common import ActionFailed
from game.actionsNew.actionBaseNew import ActionBaseNew
from game.entities import DieId, Resource, Tech, Team

class ActionTradeArgs(ActionArgs):
    receiver: Team
    production: Resource
    amount: Decimal

class ActionTrade(ActionBaseNew):

    @property
    def args(self) -> ActionTradeArgs:
        assert isinstance(self._generalArgs, ActionTradeArgs)
        return self._generalArgs


    def cost(self) -> Dict[Resource, Decimal]:
        level = self.args.production.typ[1]
        payResource = self.entities[f"mge-obchod-{level}"]
        return {payResource:ceil(self.args.amount)}


    def _commitImpl(self) -> None:
        team = self.teamState

        available = team.resources.get(self.args.production, 0)

        if self.args.production.id[:4] != "pro-":
            raise ActionFailed(f"Nelze obchodovat [[{self.args.production}]]")

        if self.args.amount > available:
            raise ActionFailed(f"Tým {self.args.receiver.name} nemá dostatek [[{self.args.production}]] (dostupné: {available}, požadováno: {self.args.amount})")

        them = self.state.teamStates[self.args.receiver]
        team.resources[self.args.production] -= self.args.amount
        them.resources[self.args.production] = them.resources.get(self.args.production, 0) + self.args.amount

        self._info += f"Úspěšně prodáno [[{self.args.production}|{self.args.amount}]] týmu {self.args.receiver.name}"
        self._notifications = {self.args.receiver: [f"Dostali jste [[{self.args.production}|{self.args.amount}]] od týmu {self.args.team.name}"]}