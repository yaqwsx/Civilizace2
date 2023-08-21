from decimal import Decimal
from math import ceil

from typing_extensions import override

from game.actions.actionBase import (
    NoInitActionBase,
    TeamActionArgs,
    TeamInteractionActionBase,
)
from game.actions.common import MessageBuilder
from game.entities import BuildingUpgrade, MapTileEntity, Resource


class BuildUpgradeArgs(TeamActionArgs):
    tile: MapTileEntity
    upgrade: BuildingUpgrade


class BuildUpgradeAction(TeamInteractionActionBase):
    @property
    @override
    def args(self) -> BuildUpgradeArgs:
        args = super().args
        assert isinstance(args, BuildUpgradeArgs)
        return args

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
        tileState = self.tile_state()

        self._ensure_strong_entity_available(self.args.upgrade)
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
        tileState = self.tile_state()

        tileState.building_upgrades.add(self.args.upgrade)
        self._info += f"Vylepšení [[{self.args.upgrade.id}]] budovy [[{self.args.upgrade.building.id}]] postaveno na poli [[{self.args.tile.id}]]."
