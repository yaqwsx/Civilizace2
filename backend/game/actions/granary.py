from decimal import Decimal
from typing import Dict
from typing_extensions import override
from game.actions.actionBase import TeamActionArgs, TeamInteractionActionBase
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
    def _commitSuccessImpl(self) -> None:
        for resource, amount in self.args.productions.items():
            if not resource.isProduction:
                self._errors += f"[[{resource.id}]] není produkce"
                continue
            if resource.typ not in [self.entities["typ-jidlo"], self.entities["typ-luxus"]]:
                self._errors += f"[[{resource.id}]] není produkce jídla ani luxusu"
                continue

            if resource not in self.teamState.granary:
                self.teamState.granary[resource] = Decimal(0)
            self.teamState.granary[resource] += amount

        self._info += f"Krmení těmito produkcemi bylo automatizováno: \n{printResourceListForMarkdown(self.args.productions)}"
