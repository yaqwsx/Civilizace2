from game.actions.actionBase import TeamActionBase, TeamActionArgs
from game.state import HomeTile
from game.entities import MapTileEntity
from game.actions.common import ActionCost, ActionException

class ActionAssignTileArgs(TeamActionArgs):
    index: int

class ActionAssignTile(TeamActionBase):
    args: ActionAssignTileArgs

    def getTileEntity(self, index: int) -> MapTileEntity:
        for tile in self.entities.tiles.values():
            if tile.index == index:
                return tile
        raise RuntimeError("No tile defined for index " + str(index))

    def cost(self) -> ActionCost:
        return ActionCost()

    def commitInternal(self) -> None:
        team = self.args.team
        map = self.state.map

        if self.args.index < 0:
            oldTile = map.getHomeTile(team)
            if oldTile == None:
                self.info.add("<<{}>> did not have any tile assigned. State not changed".format(team.id))
                return
            map.homeTiles[team] = None
            self.info.add("Home tile removed for team <<{}>>".format(team.id))
            return

        newTile = map.tiles.get(self.args.index)
        if newTile != None:
            if not isinstance(newTile, HomeTile):
                raise ActionException("New tile index is already used by a regular tile {}".format(newTile.name))
            else:
                raise ActionException("The new index is already owned by team <<{}>>".format(newTile.team.id))

        oldTile = map.getHomeTile(team)
        if oldTile != None:
            map.tiles[oldTile.entity.index] = None
            map.homeTiles[team] = None

        entity = self.getTileEntity(self.args.index)
        tile = HomeTile(entity=entity, team=team)
        map.tiles[self.args.index] = tile
        map.homeTiles[team] = tile
