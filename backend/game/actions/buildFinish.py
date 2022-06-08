from typing import Dict, Optional
from game.actions.actionBase import ActionArgs, ActionBase, ActionFailed
from game.actions.researchStart import ActionResearchArgs
from game.entities import Building, MapTileEntity, Resource, Team, Tech


class ActionBuildFinishArgs(ActionArgs):
    team: Team
    tile: MapTileEntity
    build: Building
    demolish: Optional[Building]


class ActionBuildFinish(ActionBase):

    @property
    def args(self) -> ActionBuildFinishArgs:
        assert isinstance(self._generalArgs, ActionBuildFinishArgs)
        return self._generalArgs


    def cost(self) -> Dict[Resource, int]:
        return self.state.world.buildDemolitionCost if self.args.demolish != None else {}


    def _commitImpl(self) -> None:
        tile = self.state.map.tiles[self.args.tile.index]

        if self.args.build in tile.buildings:
            self._warnings += f"Budova již na poli existuje a nelze postavit další. Směnka propadla"
            return

        if not self.args.build in tile.unfinished.get(self.args.team, []):
            raise ActionFailed(f"Budova {self.args.build.name} na poli {tile.name} neexistuje nebo nebyla dokončena. Zkontrolujte, že tým odevzdal směnku k dokončení budovy.")

        # TODO: check tile owner
    
        if tile.parcelCount == len(tile.buildings) and self.args.demolish == None:
            raise ActionFailed(f"Nedostatek parcel na poli {tile.name}. Je nutné vybrat budovu k demolici")
        if tile.parcelCount < len(tile.buildings) and self.args.demolish != None:
            raise ActionFailed(f"Nelze zbourat budovu. Na poli {tile.name} jsou ještě volné parcely")

        if self.args.demolish != None:
            tile.buildings.remove(self.args.demolish)
            self._info += f"Na poli {tile.name} byla zbořena budova {self.args.demolish.name}."
        tile.unfinished[self.args.team].remove(self.args.build)
        tile.buildings.add(self.args.build)
        self._info += f"Stavba {self.args.build.name} na poli {tile.name} dokončena a zkolaudována."
