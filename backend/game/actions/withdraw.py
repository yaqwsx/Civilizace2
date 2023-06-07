from decimal import Decimal
from typing import Dict

from typing_extensions import override

from game.actions.actionBase import TeamActionArgs, TeamInteractionActionBase
from game.actions.common import MessageBuilder
from game.entities import Resource
from game.state import printResourceListForMarkdown


class WithdrawArgs(TeamActionArgs):
    resources: Dict[Resource, int]


class WithdrawAction(TeamInteractionActionBase):
    @property
    @override
    def args(self) -> WithdrawArgs:
        assert isinstance(self._generalArgs, WithdrawArgs)
        return self._generalArgs

    @property
    @override
    def description(self) -> str:
        return f"Výběr materiálů ze skladu ({self.args.team.name})"

    @override
    def cost(self) -> Dict[Resource, int]:
        tokens = max(0, sum(self.args.resources.values()))
        return {self.entities.work: tokens, self.entities.withdraw_capacity: tokens}

    @override
    def _initiateCheck(self) -> None:
        self._ensure(len(self.args.resources) > 0, "Nejsou vybrány žádné materiály")

        for resource, amount in self.args.resources.items():
            if amount == 0:
                continue
            self._ensure(resource.isWithdrawable, f"Nelze vybrat: [[{resource.id}]]")
            self._ensure(
                amount >= 0,
                f"Nelze vybrat záporný počet materiálů: {amount}× [[{resource.id}]]",
            )
            available = self.teamState.resources.get(resource, Decimal(0))
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
