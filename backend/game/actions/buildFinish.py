from typing import Dict, Optional
from game.actions.actionBase import ActionArgs, ActionBase, ActionFailed
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

    @property
    def description(self):
        return f"Kolaudace budovy {self.args.build.name} na poli {self.args.tile.name} ({self.args.team.name})"


    def cost(self) -> Dict[Resource, int]:
        return self.state.world.buildDemolitionCost if self.args.demolish != None else {}


    def _commitImpl(self) -> None:
        tile = self.state.map.tiles[self.args.tile.index]

        if self.args.build in tile.buildings:
            self._warnings += f"Budova již na poli existuje a nelze postavit další."
            return
        if self.state.map.getOccupyingTeam(self.args.tile) != self.team:
            raise ActionFailed(f"Budovu nelze postavit, protože pole {self.args.tile.name} není v držení týmu.")


        if not self.args.build in tile.unfinished.get(self.args.team, []):
            raise ActionFailed(f"Budova {self.args.build.name} na poli {tile.name} neexistuje nebo nebyla dokončena. Zkontrolujte, že tým odevzdal směnku k dokončení budovy.")

        if (occupier := self.state.map.getOccupyingTeam(tile.entity)) != self.team:
            raise ActionFailed(f"Pole není týmem obsazeno týmu, takže budovu nyní nelze zkolaudovat.")

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
