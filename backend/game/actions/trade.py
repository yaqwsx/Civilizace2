from decimal import Decimal
from math import ceil
from typing import Dict, List, Optional, Set, Tuple
from game.actions.actionBase import ActionArgs, HealthyAction
from game.actions.common import ActionFailed
from game.actions.actionBase import ActionBase
from game.entities import DieId, Resource, Tech, Team
from game.state import printResourceListForMarkdown

class ActionTradeArgs(ActionArgs):
    team: Team
    receiver: Team
    resources: Dict[Resource, Decimal]

class ActionTrade(HealthyAction):

    @property
    def args(self) -> ActionTradeArgs:
        assert isinstance(self._generalArgs, ActionTradeArgs)
        return self._generalArgs

    @property
    def description(self):
        return f"Prodej produkce týmu {self.args.receiver.name} ({self.args.team.name})"


    def cost(self) -> Dict[Resource, Decimal]:
        cost = {}
        for resource, amount in self.args.resources.items():
            level = resource.typ[1]
            payResource = self.entities[f"mge-obchod-{level}"]
            cost[payResource] = cost.get(payResource, 0) + ceil(amount)

        return cost


    def _commitImpl(self) -> None:
        team = self.teamState

        with self._errors.startList("Obchod nelze provést") as err:
            for resource, amount in self.args.resources.items():
                available = team.resources.get(resource, 0)

                if resource.id[:4] != "pro-":
                    err(f"Nelze obchodovat [[{resource}]]")
                    continue

                if amount > available:
                    err(f"Tým {self.args.receiver.name} nemá dostatek [[{resource}]] (dostupné: {available}, požadováno: {amount})")
                    continue

                them = self.state.teamStates[self.args.receiver]
                team.resources[resource] = available - amount
                them.resources[resource] = them.resources.get(resource, 0) + amount

        self._info += f"Úspěšně prodáno týmu {self.args.receiver.name}: {printResourceListForMarkdown(self.args.resources)}"
        self._notifications = {self.args.receiver: [f"Od týmu {self.args.team.name} jste dostali {printResourceListForMarkdown(self.args.resources)}"]}
