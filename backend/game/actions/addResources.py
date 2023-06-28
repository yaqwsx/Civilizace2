from decimal import Decimal

from typing_extensions import override

from game.actions.actionBase import NoInitActionBase, TeamActionArgs
from game.actions.common import printResourceListForMarkdown
from game.entities import Resource


class AddResourcesArgs(TeamActionArgs):
    resources: dict[Resource, Decimal]


class AddResourcesAction(NoInitActionBase):
    @property
    @override
    def args(self) -> AddResourcesArgs:
        args = super().args
        assert isinstance(args, AddResourcesArgs)
        return args

    @property
    @override
    def description(self) -> str:
        return f"Přidat zdroje týmu {self.args.team.name}"

    @override
    def _commitImpl(self) -> None:
        teamState = self.team_state()
        self._ensure(
            any(value != 0 for value in self.args.resources.values()),
            "Nejsou vybrány žádné zdroje",
        )
        for resource, amount in self.args.resources.items():
            if amount == 0:
                continue
            teamState.resources.setdefault(resource, Decimal(0))
            teamState.resources[resource] += amount
            self._ensure(
                teamState.resources[resource] >= 0, f"Záporný počet [[{resource}]]"
            )

        self._info += printResourceListForMarkdown(
            self.args.resources, header=f"Tým {self.args.team.name} dostal:"
        )
