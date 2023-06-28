from math import ceil

from typing_extensions import override

from game.actions.actionBase import ActionArgs, NoInitActionBase


class NextTurnArgs(ActionArgs):
    pass


class NextTurnAction(NoInitActionBase):
    @property
    @override
    def args(self) -> NextTurnArgs:
        args = super().args
        assert isinstance(args, NextTurnArgs)
        return args

    @property
    @override
    def description(self) -> str:
        return "Další kolo"

    @override
    def _commitImpl(self) -> None:
        self.state.world.turn += 1
        self._info += f"Začalo kolo {self.state.world.turn}"

        tiles = [
            y
            for x, y in self.state.map.tiles.items()
            if x % 5 == self.state.world.turn % 5
        ]

        for tile in tiles:
            tile.richnessTokens = ceil(
                min(
                    tile.richnessTokens + (tile.entity.richness / 2),
                    tile.entity.richness,
                )
            )
