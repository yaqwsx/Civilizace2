from decimal import Decimal
from math import ceil

from typing_extensions import override

from game.actions.actionBase import (
    NoInitActionBase,
    TeamActionArgs,
    TeamActionBase,
    TeamInteractionActionBase,
    TileActionArgs,
)
from game.actions.common import MessageBuilder
from game.entities import BuildingUpgrade, Resource


class BuildUpgradeArgs(TeamActionArgs, TileActionArgs):
    upgrade: BuildingUpgrade


class BuildUpgradeAction(TeamInteractionActionBase):
    @property
    @override
    def args(self) -> BuildUpgradeArgs:
        assert isinstance(self._generalArgs, BuildUpgradeArgs)
        return self._generalArgs

    @property
    @override
    def description(self) -> str:
        return f"Vylepšení {self.args.upgrade.name} budovy {self.args.upgrade.building.name} na poli {self.args.tile.name} ({self.args.team.name})"

    @override
    def cost(self) -> dict[Resource, Decimal]:
        return self.args.upgrade.cost

    @override
    def pointsCost(self) -> int:
        return self.args.upgrade.points

    def travelTime(self) -> int:
        return self.state.map.getActualDistance(
            self.args.team, self.args.tile, self.state.teamStates
        )

    @override
    def _initiateCheck(self) -> None:
        tileState = self.args.tileState(self.state)

        self._ensureStrong(
            self.state.map.getOccupyingTeam(self.args.tile, self.state.teamStates)
            == self.args.team,
            f"Nelze postavit budovu, protože pole {self.args.tile.name} není v držení týmu.",
        )
        self._ensureStrong(
            self.args.upgrade.building in tileState.buildings,
            f"Budova {self.args.upgrade.building.name} není postavena na poli {self.args.tile.name}",
        )
        self._ensureStrong(
            self.args.upgrade not in tileState.building_upgrades,
            f"Vylepšení {self.args.upgrade.name} budovy {self.args.upgrade.building.name} je už na poli {self.args.tile.name} postaveno",
        )

    @override
    def _commitSuccessImpl(self) -> None:
        scheduled = self._scheduleAction(
            BuildUpgradeCompletedAction, self.args, self.travelTime()
        )
        self._info += f"Stavba vylepšení začala. Za {ceil(scheduled.delay_s / 60)} minut bude vylepšení dokončeno"


class BuildUpgradeCompletedAction(TeamActionBase, NoInitActionBase):
    @property
    @override
    def args(self) -> BuildUpgradeArgs:
        assert isinstance(self._generalArgs, BuildUpgradeArgs)
        return self._generalArgs

    @property
    @override
    def description(self) -> str:
        return f"Dokončení stavby vylepšení {self.args.upgrade.name} budovy {self.args.upgrade.building.name} na poli {self.args.tile.name} ({self.args.team.name})"

    @override
    def _commitImpl(self) -> None:
        tileState = self.args.tileState(self.state)

        if (
            self.state.map.getOccupyingTeam(self.args.tile, self.state.teamStates)
            != self.args.team
        ):
            # TODO: Check if this condition should stay (else add notification to the current team)
            self._warnings += f"Pole [[{self.args.tile.id}]] není v držení týmu [[{self.args.team.id}]]."
        elif self.args.upgrade.building not in tileState.buildings:
            self._warnings += f"Budova [[{self.args.upgrade.building.id}]] na poli [[{self.args.tile.id}]] neexistuje."
        elif self.args.upgrade in tileState.building_upgrades:
            self._warnings += f"Vylepšení [[{self.args.upgrade.id}]] budovy [[{self.args.upgrade.building.id}]] na poli [[{self.args.tile.id}]] už existuje."
        else:
            tileState.building_upgrades.add(self.args.upgrade)
            self._info += f"Vylepšení [[{self.args.upgrade.id}]] budovy [[{self.args.upgrade.building.id}]] postaveno na poli [[{self.args.tile.id}]]."

        msgBuilder = MessageBuilder()
        if not self._warnings.empty:
            msgBuilder += f"Stavba vylepšení [[{self.args.upgrade.id}]] budovy [[{self.args.upgrade.building.id}]] na poli [[{self.args.tile.id}]] se nezdařila:"
            msgBuilder += self._warnings

        msgBuilder += self._info
        self._addNotification(self.args.team, msgBuilder.message)
