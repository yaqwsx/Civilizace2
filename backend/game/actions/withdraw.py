from decimal import Decimal

from typing_extensions import override

from game.actions.actionBase import TeamActionArgs, TeamInteractionActionBase
from game.actions.common import MessageBuilder, printResourceListForMarkdown
from game.entities import Resource


class WithdrawArgs(TeamActionArgs):
    resources: dict[Resource, int]


class WithdrawAction(TeamInteractionActionBase):
    @property
    @override
    def args(self) -> WithdrawArgs:
        args = super().args
        assert isinstance(args, WithdrawArgs)
        return args

    @property
    @override
    def description(self) -> str:
        return f"Výběr materiálů ze skladu ({self.args.team.name})"

    @override
    def cost(self) -> dict[Resource, int]:
        tokens = max(0, sum(self.args.resources.values()))
        return {self.entities.work: tokens, self.entities.withdraw_capacity: tokens}

    @override
    def _initiateCheck(self) -> None:
        self._ensure(len(self.args.resources) > 0, "Nejsou vybrány žádné materiály")
        teamState = self.team_state()

        for resource, amount in self.args.resources.items():
            if amount == 0:
                continue
            self._ensure(resource.isWithdrawable, f"Nelze vybrat: [[{resource.id}]]")
            self._ensure(
                amount >= 0,
                f"Nelze vybrat záporný počet materiálů: {amount}× [[{resource.id}]]",
            )
            available = teamState.resources.get(resource, Decimal(0))
            self._ensure(
                amount <= available,
                f"Tým nemá dostatek [[{resource.id}]] (dostupné: {available}, požadováno: {amount})",
            )

    @override
    def _commitSuccessImpl(self) -> None:
        self._payResources(self.args.resources)

        self._info += MessageBuilder(
            "Vydejte týmu zdroje:", printResourceListForMarkdown(self.args.resources)
        )
