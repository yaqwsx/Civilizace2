from decimal import Decimal
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
from game.actions.common import MessageBuilder
from game.entities import Building, Resource


class BuildArgs(TeamActionArgs, TileActionArgs):
    building: Building


class BuildAction(TeamInteractionActionBase):
    @property
    @override
    def args(self) -> BuildArgs:
        assert isinstance(self._generalArgs, BuildArgs)
        return self._generalArgs

    @property
    @override
    def description(self) -> str:
        return f"Stavba budovy {self.args.building.name} na poli {self.args.tile.name} ({self.args.team.name})"

    @override
    def cost(self) -> Dict[Resource, Decimal]:
        return self.args.building.cost

    @override
    def pointsCost(self) -> int:
        assert self.teamState
        return self.args.building.points

    def travelTime(self) -> int:
        return ceil(self.state.map.getActualDistance(self.args.team, self.args.tile))

    @override
    def _initiateCheck(self) -> None:
        tileState = self.args.tileState(self.state)

        self._ensureStrong(
            self.state.map.getOccupyingTeam(self.args.tile) == self.args.team,
            f"Nelze postavit budovu, protože pole {self.args.tile.name} není v držení týmu.",
        )
        self._ensureStrong(
            self.args.building not in tileState.buildings,
            f"Budova {self.args.building.name} je už na poli {self.args.tile.name} postavena",
        )
        for feature in self.args.building.requiredTileFeatures:
            self._ensure(
                feature in self.args.tileState(self.state).features,
                f"Na poli {self.args.tile.name} chybí {feature.name}",
            )

    @override
    def _commitSuccessImpl(self) -> None:
        scheduled = self._scheduleAction(
            BuildCompletedAction, self.args, self.travelTime()
        )
        self._info += f"Stavba začala. Za {ceil(scheduled.delay_s / 60)} minut bude budova dokončena"


class BuildCompletedAction(TeamActionBase, NoInitActionBase):
    @property
    @override
    def args(self) -> BuildArgs:
        assert isinstance(self._generalArgs, BuildArgs)
        return self._generalArgs

    @property
    @override
    def description(self) -> str:
        return f"Dokončení stavby budovy {self.args.building.name} na poli {self.args.tile.name} ({self.args.team.name})"

    @override
    def _commitImpl(self) -> None:
        tileState = self.args.tileState(self.state)

        if self.state.map.getOccupyingTeam(self.args.tile) != self.args.team:
            # TODO: Check if this condition should stay (else add notification to the current team)
            self._warnings += f"Pole [[{self.args.tile.id}]] není v držení týmu [[{self.args.team.id}]] pro stavbu budovy [[{self.args.building.id}]]."
        elif self.args.building in tileState.buildings:
            self._warnings += f"Budova [[{self.args.building.id}]] na poli [[{self.args.tile.id}]] už existuje."
        else:
            tileState.buildings.add(self.args.building)
            self._info += f"Budova [[{self.args.building.id}]] postavena na poli [[{self.args.tile.id}]]."

        msgBuilder = MessageBuilder(
            message=f"Stavba budovy {self.args.building.name} dokončena:"
        )
        msgBuilder += self._warnings
        msgBuilder += self._info
        self._addNotification(self.args.team, msgBuilder.message)
