from decimal import Decimal

from typing_extensions import override

from game.actions.actionBase import TeamActionArgs, TeamInteractionActionBase
from game.entities import Building, MapTileEntity, Resource


class BuildArgs(TeamActionArgs):
    tile: MapTileEntity
    building: Building


class BuildAction(TeamInteractionActionBase):
    @property
    @override
    def args(self) -> BuildArgs:
        args = super().args
        assert isinstance(args, BuildArgs)
        return args

    @property
    @override
    def description(self) -> str:
        return f"Stavba budovy {self.args.building.name} na poli {self.args.tile.name} ({self.args.team.name})"

    @override
    def cost(self) -> dict[Resource, Decimal]:
        return self.args.building.cost

    @override
    def pointsCost(self) -> int:
        return self.args.building.points

    def travelTime(self) -> int:
        return self.state.map.getActualDistance(
            self.args.team, self.args.tile, self.state.teamStates
        )

    @override
    def _initiateCheck(self) -> None:
        tileState = self.tile_state()

        self._ensure_strong_entity_available(self.args.building)
        self._ensureStrong(
            self.state.map.getOccupyingTeam(self.args.tile, self.state.teamStates)
            == self.args.team,
            f"Nelze postavit budovu, protože pole {self.args.tile.name} není v držení týmu.",
        )
        self._ensureStrong(
            self.args.building not in tileState.buildings,
            f"Budova {self.args.building.name} je už na poli {self.args.tile.name} postavena",
        )
        for feature in self.args.building.requiredTileFeatures:
            self._ensure(
                feature in tileState.features,
                f"Na poli {self.args.tile.name} chybí {feature.name}",
            )

    @override
    def _commitSuccessImpl(self) -> None:
        self.tile_state().buildings.add(self.args.building)
        self._info += f"Budova [[{self.args.building.id}]] postavena na poli [[{self.args.tile.id}]]."
