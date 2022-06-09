from decimal import Decimal
from typing import Dict, Optional
from game.actions.actionBase import ActionArgs, ActionBase
from game.actions.common import ActionFailed
from game.entities import MapTileEntity, Resource, Team
from game.state import Army, ArmyGoal, ArmyMode


class ActionArmyDeployArgs(ActionArgs):
    armyIndex: int
    goal: ArmyGoal
    equipment: int
    friendlyTeam: Optional[Team] # Support mode allows chosing a team to support; should be defaulted to the team currently occupying target tile

class ArmyDeploy(ActionBase):
    pass




#========================================================
#========================================================
#========================================================
class ActionArmyDeployArgs(ActionArgs):
    team: Team
    armyName: str
    tile: MapTileEntity
    goal: ArmyGoal
    equipment: int
    friendlyTeam: Optional[Team] # Support mode allows chosing a team to support; should be defaulted to the team currently occupying target tile

class ActionArmyDeploy(ActionBase):
    args: ActionArmyDeployArgs


    def transferEquipment(self, provider: Army, receiver: Army) -> int:
        amount = min(receiver.capacity - receiver.equipment, provider.equipment)
        provider.equipment -= amount
        receiver.equipment += amount
        return amount


    def cost(self) -> Dict[Resource, Decimal]:
        return {self.entities.zbrane: self.args.equipment}


    def requiresDelayedEffect(self) -> int:
        return self.state.map.getActualDistance(self.args.team, self.args.tile)


    def commitInternal(self) -> None:
        if not self.args.army in self.teamState.armies: raise ActionFailed("Neznámá armáda {}".format(self.args.army))

        army = self.teamState.armies[self.args.army]
        if army.assignment != ArmyMode.Idle:
            assert army.tile != None, "Army {} is in inconsistent state".format(self.args.army)
            raise ActionFailed( "Armáda {} už je vyslána na pole {}."\
                    .format(army.id, army.tile))

        if self.args.equipment < 1: raise ActionFailed("Nelze poskytnout záporný počet zbraní ({}). Minimální počet je 1".format(self.args.equipment))
        if self.args.equipment > army.capacity:
            raise ActionFailed("Armáda neunese {} zbraní. Maximální možná výzbroj je {}."\
                    .format(self.args.equipment, army.capacity))

        army.tile = self.args.tile
        army.equipment = self.args.equipment
        army.assignment = ArmyMode.Marching
        army.goal = self.args.goal

        tile = self.state.map.tiles[self.args.tile.index]
        tile.inbound.add(army.id)
        self._info.add("Armáda [[{}]] vyslána na pole [[{}]]. Dorazí v [[cas]]"\
                    .format(army.id, army.tile))


    def delayedInternal(self) -> str:
        army = self.teamState.armies[self.args.army]
        tile = self.state.map.tiles[self.args.tile.index]
        defender = self.state.getArmy(tile.occupiedBy)

        if defender == None:
            if self.args.goal != ArmyGoal.Occupy and self.args.goal != ArmyGoal.Replace:
                equipment = army.retreat(self.state)
                self.reward[self.entities.zbrane] += equipment
                return "Pole [[{}]] je prázdné, armáda [[{}]] se vrátila zpět"\
                    .format(tile.entity.id, army.id)
            else:
                army.occupy(tile)
                return "Armáda [[{}]] obsadila pole [[{}]]".format(army.id, tile.entity.id)

        if defender.team == army.team:
            if self.args.goal == ArmyGoal.Eliminate:
                equipment = army.retreat(self.state)
                self.reward[self.entities.zbrane] += equipment
                return "Pole [[{}]] už bylo obsazeno jinou vaší armádou [[{}]]. Armáda [[{}]] se vrátila domů."\
                    .format(tile, tile.occupiedBy, army.id)
            provider = defender if self.args.goal == ArmyGoal.Replace else army
            receiver = army if self.args.goal == ArmyGoal.Replace else defender
            transfered = self.transferEquipment(provider, receiver)
            if self.args.goal == ArmyGoal.Replace:
                army.boost = defender.boost

            equipment = provider.retreat(self.state)
            receiver.occupy(tile)
            self.reward[self.entities.zbrane] += equipment

            if self.args.goal == ArmyGoal.Replace:
                return "Armáda [[{}]] nahradila předchozí armádu. Její nová síla je [[{}]]. Armáda [[{}]] se vrátila domů."\
                    .format(army.id, army.strength, provider.id)
            return "Armáda [[{}]] posílila armádu [[{}]] a vrátila se zpět. Nová síla obránce je [[{}]]."\
                .format(army.id, army.strength, provider.id)

        if self.args.goal == ArmyGoal.Supply and self.args.friendlyTeam == defender.team:
            transfered = self.transferEquipment(army, defender)
            equipment = army.retreat(self.state)
            self.reward[self.entities.zbrane] += equipment
            # TODO: Notify defender
            return "Armáda [[{}]] posílila armádu týmu [[{}]] o [[{}]] zbraní."\
                .format(army.id, defender.team, transfered)

        if self.args.goal == ArmyGoal.Supply:
            equipment = army.retreat(self.state)
            self.reward[self.entities.zbrane] += equipment
            self.errors.add("Pole [[{}]] je obsazeno nepřátelksou armádou. Vaše armáda [[{}]] se vrátila domů."\
                .format(tile.id, army.id))
            return

        attacker = army

        # battle
        defenderCasualties = ceil((BASE_ARMY_STRENGTH + attacker.equipment) / 2) + max(0, attacker.boost) - tile.defenseBonus
        attackerCasualties = ceil((BASE_ARMY_STRENGTH + defender.equipment) / 2) + max(0, defender.boost)

        defenderStrength = defender.destroyEquipment(defenderCasualties)
        attackertStrength = attacker.destroyEquipment(attackerCasualties)

        # resolve
        if defenderStrength >= attackertStrength:
            self.reward[self.entities.zbrane] += attacker.retreat(self.state)
            self.errors.add("Armáda [[{}]] neuspěla v dobývání pole [[{}]] a vrátila se domů.")

            if defender.equipment == 0:
                defender.retreat(self.state)
            #TODO: Notify defender
            return

        defenderReward = defender.retreat(self.state)
        #TODO: Notify defender

        if attacker.equipment == 0:
            attacker.retreat(self.state)
            return "Armáda [[{}]] dobyla pole [[{}]]. Nezbyly jí žádné zbraně, tak se vrátila domů."\
                .format(army.id, tile.entity)

        if self.args.goal == ArmyGoal.Eliminate:
            self.reward[self.entities.zbrane] += attacker.retreat(self.state)
            return "Armáda [[{}]] vyčistila pole [[{}]] a vrátila se domů".format(army,id, tile.entity)

        attacker.occupy(tile)
        return "Armáda [[{}]] obsadila pole [[{}]]. Její aktuální síla je {}".format(army.id, tile.entity, army.strength)