from math import ceil
from typing import Dict

from typing_extensions import override

from game.actions.actionBase import (
    NoInitActionBase,
    TeamActionArgs,
    TeamActionBase,
    TeamInteractionActionBase,
    TileActionArgs,
)
from game.entities import Resource


class BuildRoadArgs(TeamActionArgs, TileActionArgs):
    pass


class BuildRoadAction(TeamInteractionActionBase):
    @property
    @override
    def args(self) -> BuildRoadArgs:
        assert isinstance(self._generalArgs, BuildRoadArgs)
        return self._generalArgs

    @property
    @override
    def description(self) -> str:
        return f"Stavba cesty na pole {self.args.tile.name} ({self.args.team.name})"

    @override
    def cost(self) -> Dict[Resource, int]:
        return self.state.world.roadCost

    @override
    def pointsCost(self) -> int:
        return self.state.world.roadPointsCost

    def travelTime(self) -> int:
        return ceil(
            2
            * self.state.map.getActualDistance(
                self.args.team, self.args.tile, self.state.teamStates
            )
        )

    @override
    def _initiateCheck(self) -> None:
        self._ensureStrong(
            self.args.tile not in self.teamState.roadsTo,
            f"Na pole {self.args.tile.name} je už cesta postavena",
        )
        self._ensureStrong(
            self.state.map.getOccupyingTeam(self.args.tile, self.state.teamStates)
            == self.args.team,
            f"Nelze postavit cestu, protože pole {self.args.tile.name} není v držení týmu.",
        )

    @override
    def _commitSuccessImpl(self) -> None:
        scheduled = self._scheduleAction(
            BuildRoadCompletedAction, args=self.args, delay_s=self.travelTime()
        )
        self._info += f"Stavba cesty začala. Za {ceil(scheduled.delay_s / 60)} minut bude dokončena."


class BuildRoadCompletedAction(TeamActionBase, NoInitActionBase):
    @property
    @override
    def args(self) -> BuildRoadArgs:
        assert isinstance(self._generalArgs, BuildRoadArgs)
        return self._generalArgs

    @property
    @override
    def description(self) -> str:
        return f"Stavba cesty na pole {self.args.tile.name} ({self.args.team.name})"

    @override
    def _commitImpl(self) -> None:
        # TODO check tile owner based on rules

        self.teamState.roadsTo.add(self.args.tile)
        self._info += f"Cesta na pole {self.args.tile.name} dokončena."
