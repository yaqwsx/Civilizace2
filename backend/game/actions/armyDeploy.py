from enum import Enum
from typing import Optional
from pydantic import BaseModel
from game.entities import BASE_ARMY_STRENGTH

from game.actions.actionBase import TeamActionArgs, TeamActionBase
from game.actions.common import ActionCost, ActionException
from game.entities import Team, MapTileEntity, MapTileEntity
from game.state import Army, ArmyId, ArmyState

class ArmyGoal(Enum):
    Occupy = 0
    Eliminate = 1
    Support = 2
    Replace = 3

class ActionArmyDeployArgs(TeamActionArgs):
    army: ArmyId
    tile: MapTileEntity
    goal: ArmyGoal
    equipment: int
    friendlyTeam: Optional[Team] # Support mode allows chosing a team to support; should be defaulted to the team currently occupying target tile

class ActionArmyDeploy(TeamActionBase):
    args: ActionArmyDeployArgs

    def transferEquipment(self, provider: Army, receiver: Army) -> int:
        amount = min(receiver.capacity - receiver.equipment, provider.equipment)
        provider.equipment -= amount
        receiver.equipment += amount
        return amount


    def cost(self) -> ActionCost:
        return ActionCost(postpone=self.state.map.getActualDistance(self.args.team, self.args.tile),
                          resources={self.entities.zbrane: self.args.equipment})


    def commitInternal(self) -> None:
        if not self.args.army in self.teamState.armies: raise ActionException("Neznámá armáda {}".format(self.args.army))
        
        army = self.teamState.armies[self.args.army]
        if army.state != ArmyState.Idle:
            assert army.tile != None, "Army {} is in inconsistent state".format(self.args.army)
            raise ActionException( "Armáda {} už je vyslána na pole {}."\
                    .format(army.id, army.tile))
        
        if self.args.equipment < 0: raise ActionException("Nelze poskytnout záporný počet zbraní ({})".format(self.args.equipment))
        if self.args.equipment > army.capacity:
            raise ActionException("Armáda neunese {} zbraní. Maximální možná výzbroj je {}."\
                    .format(self.args.equipment, army.capacity))
        
        army.tile = self.args.tile
        army.equipment = self.args.equipment
        army.state = ArmyState.Marching
        self.info.add("Armáda <<{}>> vyslána na pole <<{}>>. Dorazí v <<cas>>"\
                    .format(army.id, army.tile))


    def delayed(self) -> str:
        army = self.teamState.armies[self.args.army]
        tile = self.state.map.tiles[self.args.tile.index]
        defender = self.state.getArmy(tile.occupiedBy)

        if defender == None:
            if self.args.goal != ArmyGoal.Occupy:
                equipment = army.retreat()
                self.reward[self.entities.zbrane] += equipment
                return "Pole <<{}>> je prázdné, armáda <<{}>> se vrátila zpět"\
                    .format(tile.id, army.id)
            else:
                tile.occupiedBy = army.id
                army.state = ArmyState.Occupying
                army.boost = 0
                return "Armáda <<{}>> obsadila pole <<{}>>".format(army.id, tile.entity.id)

        if defender.team == army.team:
            if self.args.goal == ArmyGoal.Eliminate:
                equipment = army.retreat()
                self.reward[self.entities.zbrane] += equipment
                return "Pole <<{}>> už bylo obsazeno jinou vaší armádou <<{}>>. Armáda <<{}>> se vrátila domů."\
                    .format(tile, tile.occupiedBy, army.id)
            provider = defender if self.args.goal == ArmyGoal.Replace else army
            receiver = army if self.args.goal == ArmyGoal.Replace else defender
            transfered = self.transferEquipment(provider, receiver)

            tile.occupiedBy = receiver
            receiver.occupy(tile)
            equipment = provider.retreat()
            self.reward[self.entities.zbrane] += equipment

            if self.args.goal == ArmyGoal.Replace:
                return "Armáda <<{}>> nahradila předchozí armádu. Její nová síla je <<{}>>. Armáda <<{}>> se vrátila domů."\
                    .format(army.id, army.strength, provider.id)

        if self.args.goal == ArmyGoal.Support and self.args.friendlyTeam == defender.team:
            transfered = self.transferEquipment(army, defender)
            equipment = army.retreat()
            self.reward[self.entities.zbrane] += equipment
            # TODO: Notify defender
            return "Armáda <<{}>> posílila armádu týmu <<{}>> o <<{}>> zbraní."\
                .format(army.id, defender.team, transfered)

        if self.args.goal == ArmyGoal.Support or self.args.goal == ArmyGoal.Replace:
            equipment = army.retreat()
            self.reward[self.entities.zbrane] += equipment
            return "Pole <<{}>> je obsazeno nepřátelksou armádou. Vaše armáda <<{}>> se vrátila domů."\
                .format(tile.id, army.id)
        
        raise RuntimeError("Souboje jeste nejsou implementovany")
        # battle



        
        

