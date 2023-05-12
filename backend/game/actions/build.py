from decimal import Decimal
from math import ceil
from typing import Dict, Iterable, Tuple

from typing_extensions import override

from game.actions.actionBase import (NoInitActionBase, TeamActionArgs,
                                     TeamActionBase, TeamInteractionActionBase,
                                     TileActionArgs)
from game.actions.common import MessageBuilder
from game.entities import Building, Die, Resource


class BuildArgs(TeamActionArgs, TileActionArgs):
    build: Building


class BuildAction(TeamInteractionActionBase):
    @property
    @override
    def args(self) -> BuildArgs:
        assert isinstance(self._generalArgs, BuildArgs)
        return self._generalArgs

    @property
    @override
    def description(self) -> str:
        return f"Stavba budovy {self.args.build.name} na poli {self.args.tile.name} ({self.args.team.name})"

    @override
    def cost(self) -> Dict[Resource, Decimal]:
        return self.args.build.cost

    @override
    def diceRequirements(self) -> Tuple[Iterable[Die], int]:
        assert self.teamState
        return (self.teamState.getUnlockingDice(self.args.build), self.args.build.points)

    def travelTime(self) -> int:
        return ceil(self.state.map.getActualDistance(self.args.team, self.args.tile))

    @override
    def _initiateCheck(self) -> None:
        tileState = self.args.tileState(self.state)

        self._ensureStrong(self.state.map.getOccupyingTeam(self.args.tile) == self.args.team,
                           f"Nelze postavit budovu, protože pole {self.args.tile.name} není v držení týmu.")
        self._ensureStrong(self.args.build not in tileState.buildings,
                           f"Budova {self.args.build.name} je už na poli {self.args.tile.name} postavena")
        for feature in self.args.build.requiredFeatures:
            self._ensure(feature in self.args.tileState(self.state).features,
                         f"Na poli {self.args.tile.name} chybí {feature.name}")

    @override
    def _commitSuccessImpl(self) -> None:
        scheduled = self._scheduleAction(BuildCompletedAction, self.args, self.travelTime())
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
        return f"Dokončení stavby budovy {self.args.build.name} na poli {self.args.tile.name} ({self.args.team.name})"

    @override
    def _commitImpl(self) -> None:
        tileState = self.args.tileState(self.state)

        if self.args.team not in tileState.unfinished:
            tileState.unfinished[self.args.team] = set()
        tileState.unfinished[self.args.team].add(self.args.build)
        self._info += f"Budova [[{self.args.build.id}]] postavena na poli [[{self.args.tile.id}]]"

        if tileState.parcelCount <= len(tileState.buildings):
            self._warnings += f"Pole [[{self.args.tile.id}]] nemá místo pro další budovu. Pro kolaudaci je potřeba demolice jiné budovy."

        msgBuilder = MessageBuilder(message=f"Stavba budovy {self.args.build.name} dokončena:")
        msgBuilder += self._warnings
        msgBuilder += self._info
        self._addNotification(self.args.team, msgBuilder.message)
