from decimal import Decimal
from typing import Dict

from typing_extensions import override

from game.actions.actionBase import TeamActionArgs, TeamInteractionActionBase
from game.entities import Resource, TeamAttribute


class AcquireTeamAttributeArgs(TeamActionArgs):
    attribute: TeamAttribute


class AcquireTeamAttributeAction(TeamInteractionActionBase):
    @property
    @override
    def args(self) -> AcquireTeamAttributeArgs:
        assert isinstance(self._generalArgs, AcquireTeamAttributeArgs)
        return self._generalArgs

    @property
    @override
    def description(self) -> str:
        return f"Získání týmové vlastnosti {self.args.attribute} týmem {self.args.team.name}"

    @override
    def cost(self) -> Dict[Resource, Decimal]:
        return self.args.attribute.cost

    @override
    def pointsCost(self) -> int:
        return self.args.attribute.points

    @override
    def _initiateCheck(self) -> None:
        self._ensureStrong(
            self.args.attribute not in self.teamState.attributes,
            f"Tým {self.args.team.name} už má vlastnost {self.args.attribute.name}",
        )

    @override
    def _commitSuccessImpl(self) -> None:
        self.teamState.attributes.add(self.args.attribute)
        self._info += f"Tým [[{self.args.team.id}]] obdržel vlastnost [[{self.args.attribute.id}]]."
