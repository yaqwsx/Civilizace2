from decimal import Decimal
from math import ceil, floor
from typing import Dict, List, Optional, Set, Tuple
from game.actions.actionBase import ActionArgs
from game.actions.actionBase import ActionBase, ActionResult
from game.actions.common import ActionFailed
from game.entities import Building, DieId, MapTileEntity, Resource, Team, Vyroba
from game.entityParser import DICE_IDS
from game.state import ArmyGoal

class ActionBuildRoadArgs(ActionArgs):
    team: Team
    tile: MapTileEntity


class ActionBuildRoad(ActionBase):

    @property
    def args(self) -> ActionBuildRoadArgs:
        assert isinstance(self._generalArgs, ActionBuildRoadArgs)
        return self._generalArgs


    @property
    def description(self):
        return f"Stavba cesty na pole {self.args.tile.name} ({self.args.team.name})"

    def cost(self) -> Dict[Resource, Decimal]:
        return self.state.world.roadCost


    def diceRequirements(self) -> Tuple[Set[DieId], int]:
        return (DICE_IDS, self.state.world.roadPoints)


    def requiresDelayedEffect(self) -> int:
        return self.state.map.getActualDistance(self.args.team, self.args.tile)*2


    def _commitImpl(self) -> None:
        if self.args.tile in self.teamState.roadsTo:
            raise ActionFailed(f"Na pole {self.args.tile.name} je už cesta postavena")
        
        if self.state.map.getOccupyingTeam(self.args.tile) != self.team:
            raise ActionFailed(f"Nelze postavit cestu, protože pole {self.args.tile.name} není v držení týmu.")

        self._info += f"Stavba cesty začala. Za {ceil(self.requiresDelayedEffect() / 60)} minut ji můžete přijít dokončit"


    def _applyDelayedReward(self) -> None:
        self._setupPrivateAttrs()
        tile = self.state.map.tiles[self.args.tile.index]

        self.teamState.roadsTo.add(self.args.tile)
        self._info += f"Cesta na pole {self.args.tile.name} dokončena."

