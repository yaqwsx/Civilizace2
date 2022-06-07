from typing import Dict
from game.actions.actionBase import ActionArgs
from game.actions.common import ActionFailed
from game.actions.actionBase import ActionBase
from game.entities import Resource, Team, Tech
from game.state import printResourceListForMarkdown


class ActionWithdrawArgs(ActionArgs):
    team: Team
    resources: Dict[Resource, int]


class ActionWithdraw(ActionBase):

    @property
    def args(self) -> ActionWithdrawArgs:
        assert isinstance(self._generalArgs, ActionWithdrawArgs)
        return self._generalArgs


    def _commitImpl(self) -> None:
        missing = {}
        for resource, amount in self.args.resources.items():
            stored = self.teamState.storage.get(resource, 0)
            self.teamState.storage[resource] = stored - amount
            if stored < amount:
                missing[resource] = stored -amount

        if missing != {}:
            raise ActionFailed(f"Chybí zdroje ve skladu: {printResourceListForMarkdown(missing)}")

        self.teamState.payResources({self.entities.work: sum(self.args.resources.values())})

        self._info += f"Vydejte týmu zdroje: {printResourceListForMarkdown(self.args.resources)}"
