from decimal import Decimal
from typing import Optional

from typing_extensions import override

from game.actions.actionBase import TeamActionArgs, TeamInteractionActionBase
from game.entities import Resource, Tech


class ResearchArgs(TeamActionArgs):
    tech: Tech
    task: Optional[str] = None


class ResearchStartAction(TeamInteractionActionBase):
    @property
    @override
    def args(self) -> ResearchArgs:
        assert isinstance(self._generalArgs, ResearchArgs)
        return self._generalArgs

    @property
    @override
    def description(self) -> str:
        return f"Výzkum technologie {self.args.tech.name} ({self.args.team.name})"

    @override
    def cost(self) -> dict[Resource, Decimal]:
        return self.args.tech.cost

    @override
    def pointsCost(self) -> int:
        return self.args.tech.points

    @override
    def _initiateCheck(self) -> None:
        self._ensureStrong(
            self.args.tech not in self.teamState.techs,
            f"Technologie [[{self.args.tech.id}]] je již vyzkoumána",
        )
        self._ensureStrong(
            self.args.tech not in self.teamState.researching,
            f"Výzkum technologie [[{self.args.tech.id}]] již probíhá",
        )

    @override
    def _commitSuccessImpl(self) -> None:
        if self.args.task is None:
            self._warnings += "**Pozor:** k výzkumu nebyl vybrán úkol."
        else:
            self._info += f"Zadejte týmu úkol {self.args.task}"

        self.teamState.researching.add(self.args.tech)
        self._info += f"Výzkum technologie [[{self.args.tech.id}]] začal."
