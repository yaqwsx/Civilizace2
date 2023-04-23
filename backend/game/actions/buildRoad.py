from decimal import Decimal
from math import ceil, floor
from typing import Dict, Iterable, List, Optional, Set, Tuple
from game.actions.actionBase import ActionArgs, ActionBase, ActionResult
from game.actions.common import ActionFailed
from game.entities import Building, Die, MapTileEntity, Resource, Team, Vyroba
from game.state import ArmyGoal

class BuildRoadArgs(ActionArgs):
    team: Team
    tile: MapTileEntity


class BuildRoadAction(ActionBase):

    @property
    def args(self) -> BuildRoadArgs:
        assert isinstance(self._generalArgs, BuildRoadArgs)
        return self._generalArgs


    @property
    def description(self):
        return f"Stavba cesty na pole {self.args.tile.name} ({self.args.team.name})"

    def cost(self) -> Dict[Resource, Decimal]:
        return {res: Decimal(cost) for res, cost in self.state.world.roadCost.items()}


    def diceRequirements(self) -> Tuple[Iterable[Die], int]:
        return (self.entities.dice.values(), self.state.world.roadPoints)


    def requiresDelayedEffect(self) -> Decimal:
        return 2 * self.state.map.getActualDistance(self.args.team, self.args.tile)


    def _commitImpl(self) -> None:
        assert self.teamState is not None
        if self.args.tile in self.teamState.roadsTo:
            raise ActionFailed(f"Na pole {self.args.tile.name} je už cesta postavena")

        if self.state.map.getOccupyingTeam(self.args.tile) != self.team:
            raise ActionFailed(f"Nelze postavit cestu, protože pole {self.args.tile.name} není v držení týmu.")

        self._info += f"Stavba cesty začala. Za {ceil(self.requiresDelayedEffect() / 60)} minut ji můžete přijít dokončit"


    def _applyDelayedReward(self) -> None:
        assert self.teamState is not None
        self._setupPrivateAttrs()
        tile = self.state.map.tiles[self.args.tile.index]

        self.teamState.roadsTo.add(self.args.tile)
        self._info += f"Cesta na pole {self.args.tile.name} dokončena."

