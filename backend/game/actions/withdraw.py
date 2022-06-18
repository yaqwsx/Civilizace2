from typing import Dict
from game.actions.actionBase import ActionArgs, HealthyAction
from game.actions.common import ActionFailed
from game.actions.actionBase import ActionBase
from game.entities import Resource, Team, Tech
from game.state import printResourceListForMarkdown


class ActionWithdrawArgs(ActionArgs):
    team: Team
    resources: Dict[Resource, int]


class ActionWithdraw(HealthyAction):

    @property
    def args(self) -> ActionWithdrawArgs:
        assert isinstance(self._generalArgs, ActionWithdrawArgs)
        return self._generalArgs

    @property
    def description(self):
        return f"Výběr materiálů ze skladu ({self.args.team.name})"


    def cost(self):
        return {}

    def _commitImpl(self) -> None:
        missing = {}
        empty = []
        for resource, amount in self.args.resources.items():
            if amount == 0:
                continue
            stored = self.teamState.storage.get(resource, 0)
            if amount > stored:
                missing[resource] = amount - stored
                continue
            self.teamState.storage[resource] = stored - amount

        for resource, amount in self.args.resources.items():
            if amount == 0:
                empty.append(resource)
        for resource in empty:
            del self.teamState.storage[resource]

        if missing != {}:
            raise ActionFailed(f"Chybí zdroje ve skladu:\n\n{printResourceListForMarkdown(missing)}")

        self.payResources({self.entities.work: sum(self.args.resources.values())})

        self._info += f"Vydejte týmu zdroje: \n{printResourceListForMarkdown(self.args.resources)}"
