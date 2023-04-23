from decimal import Decimal
from math import ceil, floor
from typing import Dict
from pydantic import BaseModel
from game.actions.actionBase import ActionArgs
from game.actions.actionBase import ActionBase
from game.entities import Resource

class NextTurnArgs(ActionArgs):
    pass

class NextTurnAction(ActionBase):
    @property
    def description(self):
        return "Další kolo"

    @property
    def args(self) -> NextTurnArgs:
        assert isinstance(self._generalArgs, NextTurnArgs)
        return self._generalArgs


    def cost(self) -> Dict[Resource, Decimal]:
        return {}


    def _commitImpl(self) -> None:
        self.state.world.turn += 1
        self._info += f"Začalo kolo {self.state.world.turn}"

        tiles = [y for x, y in self.state.map.tiles.items() if x % 5 == self.state.world.turn % 5]

        for tile in tiles:
            tile.richnessTokens = ceil(min(tile.richnessTokens + (tile.entity.richness / 2), tile.entity.richness))
