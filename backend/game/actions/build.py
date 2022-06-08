from decimal import Decimal
from math import ceil, floor
from typing import Dict, List, Optional, Set, Tuple
from game.actions.actionBase import ActionArgs
from game.actions.ArmyDeploy import ActionArmyDeployArgs
from game.actions.actionBase import ActionBase, ActionResult
from game.actions.common import ActionFailed
from game.entities import Building, DieId, MapTileEntity, Resource, Team, Vyroba
from game.state import MapTile, printResourceListForMarkdown

class ActionBuildArgs(ActionArgs):
    team: Team
    build: Building
    tile: MapTileEntity
    army: Optional[ActionArmyDeployArgs]


class ActionBuild(ActionBase):

    @property
    def args(self) -> ActionBuildArgs:
        assert isinstance(self._generalArgs, ActionBuildArgs)
        return self._generalArgs


    def cost(self) -> Dict[Resource, Decimal]:
        return self.args.build.cost


    def diceRequirements(self) -> Tuple[Set[DieId], int]:
        return self.teamState.getUnlockingDice(self.args.build)


    def requiresDelayedEffect(self) -> int:
        return self.state.map.getActualDistance(self.args.team, self.args.tile)


    def _commitImpl(self) -> None:
        self._info += f"Stavba začala. Za {ceil(self.requiresDelayedEffect() / 60)} minut můžete budovu přijít dokončit"


    def _applyDelayedReward(self) -> None:
        self._setupPrivateAttrs()
        tile = self.state.map.tiles[self.args.tile.index]

        unfinished = tile.unfinished.get(self.args.team, set())
        unfinished.add(self.args.build)
        tile.unfinished[self.args.team] = unfinished
        self._info += f"Budova {self.args.build.name} postavena na poli {tile.name}"

        if tile.parcelCount < len(tile.buildings):
            self._warnings += f"Překročen limit budov na daném poli. Vyberte od týmu zdroje na demolici budovy a upravte v systému stav pole, aby odpovídal stavu na mapě."
