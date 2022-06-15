from decimal import Decimal
from typing import Dict
from game.actions.actionBase import ActionArgs, HealthyAction
from game.actions.actionBase import ActionResult
from game.actions.common import ActionFailed
from game.entities import MapTileEntity, Resource, Team

class DiscoverTileArgs(ActionArgs):
    team: Team
    tile: MapTileEntity

class ActionDiscoverTile(HealthyAction):

    @property
    def args(self) -> DiscoverTileArgs:
        assert isinstance(self._generalArgs, DiscoverTileArgs)
        return self._generalArgs


    @property
    def description(self):
        return f"Objevit dílek mapy {self.args.tile.name} týmem {self.args.tile.name}"

    def cost(self) -> Dict[Resource, Decimal]:
        return {}

    def applyInitiate(self) -> ActionResult:
        for tState in self.state.teamStates.values():
            if self.args.tile in tState.discoveredTiles:
                raise ActionFailed(f"Dílek [[{self.args.tile.id}]] už byl objeven týmem {tState.team.name}.")
        return super().applyInitiate()

    def _commitImpl(self) -> None:
        tState = self.teamState
        tState.discoveredTiles.add(self.args.tile)
        self._info.add(f"Dílek [[{self.args.tile.id}]] byl objeven.")
