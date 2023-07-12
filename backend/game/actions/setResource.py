from decimal import Decimal
from typing import Literal

from typing_extensions import override

from game.actions.actionBase import NoInitActionBase, TeamActionArgs
from game.actions.common import ActionFailed
from game.entities import Resource


class SetResourceArgs(TeamActionArgs):
    resource: Resource
    old_amount: Decimal
    new_amount: Decimal


class SetResourceAction(NoInitActionBase):
    @property
    @override
    def args(self) -> SetResourceArgs:
        args = super().args
        assert isinstance(args, SetResourceArgs)
        return args

    @property
    @override
    def description(self) -> str:
        return f"Nastavit zdroj {self.args.resource.name}: {self.args.old_amount} -> {self.args.new_amount} týmu {self.args.team.name}"

    @override
    def _commitImpl(self) -> None:
        team_state = self.team_state()

        self._ensureStrong(
            self.args.new_amount >= 0, "Nelze nastavit zdroj na zápornou hodnotu"
        )

        old_amount = team_state.resources.get(self.args.resource, Decimal(0))
        self._ensureStrong(
            self.args.old_amount == old_amount,
            f"Původní počet zdrojů neodpovídá (očekáváno {self.args.old_amount}, reálně tým má {old_amount})",
        )

        team_state.resources[self.args.resource] = self.args.new_amount
        self._info += f"Tým nyní má {self.args.new_amount}× [[{self.args.resource.id}]]. (Dostal {self.args.new_amount - old_amount}×.)"
