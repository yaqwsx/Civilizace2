from decimal import Decimal
from typing import Dict
from typing_extensions import override
from game.actions.actionBase import TeamActionArgs, TeamInteractionActionBase
from game.actions.common import MessageBuilder
from game.entities import Resource
from game.state import printResourceListForMarkdown


class GranaryArgs(TeamActionArgs):
    # int is here on purpose - it does not make sense to use fractions of food
    productions: Dict[Resource, int]


class GranaryAction(TeamInteractionActionBase):
    @property
    @override
    def args(self) -> GranaryArgs:
        assert isinstance(self._generalArgs, GranaryArgs)
        return self._generalArgs

    @property
    @override
    def description(self) -> str:
        return f"Automatizace krmení ({self.args.team.name})"

    @override
    def cost(self) -> Dict[Resource, int]:
        return self.args.productions

    @override
    def _initiateCheck(self) -> None:
        self._ensure(len(self.args.productions) > 0, "Není vybráno co automatizovat")

        for resource, amount in self.args.productions.items():
            if amount == 0:
                continue
            self._ensure(
                resource.isProduction,
                f"Nelze automatizovat [[{resource.id}]] - není produkce",
            )
            self._ensure(
                amount >= 0,
                f"Nelze automatizovat záporné množství {amount}×[[{resource.id}]]",
            )

    @override
    def _commitSuccessImpl(self) -> None:
        for resource, amount in self.args.productions.items():
            if resource not in self.teamState.granary:
                self.teamState.granary[resource] = Decimal(0)
            self.teamState.granary[resource] += amount

        self._info += MessageBuilder(
            "Krmení těmito produkcemi bylo automatizováno:",
            printResourceListForMarkdown(self.args.productions),
        )
