from typing_extensions import override

from game.actions.actionBase import (
    TeamActionArgs,
    TeamInteractionActionBase,
    TileActionArgs,
)


class DiscoverTileArgs(TeamActionArgs, TileActionArgs):
    pass


class DiscoverTileAction(TeamInteractionActionBase):
    @property
    @override
    def args(self) -> DiscoverTileArgs:
        assert isinstance(self._generalArgs, DiscoverTileArgs)
        return self._generalArgs

    @property
    @override
    def description(self) -> str:
        return f"Objevit dílek mapy {self.args.tile.name} týmem {self.args.team.name}"

    @override
    def _initiateCheck(self) -> None:
        for tState in self.state.teamStates.values():
            self._ensureStrong(
                self.args.tile not in tState.discoveredTiles,
                f"Dílek [[{self.args.tile.id}]] už byl objeven týmem {tState.team.name}.",
            )

    @override
    def _commitSuccessImpl(self) -> None:
        self.teamState.discoveredTiles.add(self.args.tile)
        self._info += f"Dílek [[{self.args.tile.id}]] byl objeven."
