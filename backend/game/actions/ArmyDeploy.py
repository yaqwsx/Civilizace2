from decimal import Decimal
from math import ceil, floor
import random
from typing import Dict, Optional

from pydantic import PrivateAttr
from game.actions.actionBase import ActionArgs, ActionBase, HealthyAction
from game.actions.common import ActionFailed
from game.entities import BASE_ARMY_STRENGTH, MapTileEntity, Resource, Team
from game.state import Army, ArmyGoal, ArmyMode, MapTile


class ActionArmyDeployArgs(ActionArgs):
    team: Team
    armyIndex: int
    tile: MapTileEntity
    goal: ArmyGoal
    equipment: int
    friendlyTeam: Optional[Team] # Support mode allows chosing a team to support; should be defaulted to the team currently occupying target tile

class ActionArmyDeploy(HealthyAction):

    @property
    def args(self) -> ActionArmyDeployArgs:
        assert isinstance(self._generalArgs, ActionArmyDeployArgs)
        return self._generalArgs

    @property
    def army(self) -> Army:
        return self.state.map.armies[self.args.armyIndex]

    @property
    def map(self):
        return self.state.map

    @property
    def tile(self) -> MapTile:
        return self.state.map.getTileById(self.args.tile.id)

    @property
    def description(self):
        return f"Vyslání armády {self.army.name} na pole {self.tile.name} ({self.args.team.name})"


    def transferEquipment(self, provider: Army, receiver: Army) -> int:
        amount = min(receiver.capacity - receiver.equipment, provider.equipment)
        provider.equipment -= amount
        receiver.equipment += amount
        return amount


    def cost(self) -> Dict[Resource, Decimal]:
        if self.army.capacity < self.args.equipment:
            raise ActionFailed(f"Kapacita armády je {self.army.capacity}")
        if self.args.equipment <= 0:
            raise ActionFailed(f"Nelze vyslat nevybavenou armádu")
        return {self.entities.zbrane: self.args.equipment}


    def requiresDelayedEffect(self) -> int:
        return self.state.map.getActualDistance(self.army.team, self.args.tile)


    def _returnWeaponsInfo(self, amount: int) -> None:
        self._info += f"Vydejte týmu [[{self.entities.zbrane}|{floor(amount)}]]"


    def _commitImpl(self) -> None:
        if not self.army in self.map.armies: raise ActionFailed(f"Neznámá armáda {self.army.name}({self.army.index})")
        if self.army.team != self.team: raise ActionFailed(f"Nelze vyslat armádu cizího týmu")

        army = self.army
        if army.mode != ArmyMode.Idle:
            assert army.tile != None, "Army {} is in inconsistent state".format(self.army)
            raise ActionFailed( "Armáda {} už je vyslána na pole {}."\
                    .format(army.name, army.tile.name))

        if self.args.equipment < 1:
            raise ActionFailed(f"Nelze poskytnout záporný počet zbraní ({self.args.equipment}). Minimální počet je 1")
        if self.args.equipment > army.capacity:
            raise ActionFailed(f"Armáda neunese {self.args.equipment} zbraní. Maximální možná výzbroj je {army.capacity}.")

        army.tile = self.args.tile
        army.equipment = self.args.equipment
        army.mode = ArmyMode.Marching
        army.goal = self.args.goal

        self._info.add(f"Armáda [[{army.name}]] vyslána na pole [[{self.tile.name}]]")


    def _applyDelayedEffect(self) -> None:
        army = self.army
        tile = self.tile
        defender = self.map.getOccupyingArmy(tile.entity)

        if defender == None:
            if self.args.goal != ArmyGoal.Occupy and self.args.goal != ArmyGoal.Replace:
                equipment = self.map.retreatArmy(army)
                self._info += f"Pole {tile.entity.name} je prázdné, armáda {army.name} se vrátila zpět"
                self._returnWeaponsInfo(equipment)
                return
            else:
                self.map.occupyTile(army, tile)
                self._info += f"Armáda {army.name} obsadila pole {tile.name}"
                return

        if defender.team == army.team:
            if self.args.goal == ArmyGoal.Eliminate:
                equipment = self.map.retreatArmy(army)
                self._info += f"Pole {tile.name} už bylo obsazeno vaší armádou {defender.name}. \
                    Armáda {army.name} se vrátila domů."
                self._returnWeaponsInfo(equipment)
                return

            provider = defender if self.args.goal == ArmyGoal.Replace else army
            receiver = army if self.args.goal == ArmyGoal.Replace else defender
            transfered = self.transferEquipment(provider, receiver)
            if self.args.goal == ArmyGoal.Replace:
                army.boost = defender.boost

            equipment = self.map.retreatArmy(provider)
            if self.args.goal == ArmyGoal.Replace:
                self.map.occupyTile(receiver, tile)

            if self.args.goal == ArmyGoal.Replace:
                self._info += f"Armáda {army.name} nahradila předchozí armádu.\
                    Její nová síla je {army.strength}.\
                    Armáda {defender.name} se vrátila domů."
            else: self._info += f"Armáda {provider.name} posílila armádu {receiver.name} a vrátila se zpět.\
                Nová síla bránící armády je {receiver.strength}."
            self._returnWeaponsInfo(equipment)
            return

        if self.args.goal == ArmyGoal.Supply and self.args.friendlyTeam == defender.team:
            transfered = self.transferEquipment(army, defender)
            equipment = self.map.retreatArmy(army)

            self._info += f"Armáda {army.name} posílila armádu týmu [[{self.args.friendlyTeam}]] o {transfered} zbraní."
            self._returnWeaponsInfo(equipment)

            self.addNotification(defender.team, f"Tým [[{army.team}]] posílil vaši armádu {defender.name} na poli {tile.name} o {transfered} zbraní.\n\
                Nová síla armády {defender.name} je {defender.strength}.")
            return

        if self.args.goal == ArmyGoal.Supply:
            equipment = self.map.retreatArmy(army)
            self._warnings += f"Pole {tile.name} je obsazeno nepřátelksou armádou. Vaše armáda {army.name} se vrátila domů."
            self._returnWeaponsInfo(equipment)
            return

        attacker = army

        # battle
        defenderCasualties = ceil((BASE_ARMY_STRENGTH + attacker.equipment) / 2) + max(0, attacker.boost)
        attackerCasualties = ceil((BASE_ARMY_STRENGTH + defender.equipment) / 2) + max(0, defender.boost)

        # randomize
        r = self.state.world.combatRandomness
        defenderRandom = 1 + random.uniform(0, r) - random.uniform(0, r)
        attackerRandom = 1 + random.uniform(0, r) - random.uniform(0, r)
        defenderCasualties *= defenderRandom
        attackerCasualties *= attackerRandom

        # prevent damage
        defenderShield = max(attackerCasualties - attacker.strength, 0)
        attackerShield = max(defenderCasualties - defender.strength, 0)

        defenderLoss = defender.destroyEquipment(ceil(max(defenderCasualties - defenderShield, 0)))
        attackertLoss = attacker.destroyEquipment(ceil(max(attackerCasualties - attackerShield, 0)))

        # resolve
        if defender.strength >= attacker.strength:
            self._warnings += f"Armáda {army.name} neuspěla v dobývání pole {tile.name} a vrátila se domů."
            self._returnWeaponsInfo(self.map.retreatArmy(army))

            if defender.equipment == 0:
                self.map.retreatArmy(defender)
                self.addNotification(defender.team, f"Armáda {defender.name} ubránila pole {tile.name}, ale utrpěla vysoké ztráty a vrátila se domů.")
            return

        defenderReward = self.map.retreatArmy(defender)
        self.addNotification(defender.team, f"Armáda {defender.name} byla poražena na poli {tile.name} a vrátila se domů." +
            f" Do skladu vám bylo uloženo {defenderReward} zbraní, které jí po souboji zůstaly" if defenderReward > 0 else "")

        if army.equipment == 0:
            self.map.retreatArmy()
            self._info += f"Armáda {army.name} dobyla pole {tile.name}. Nezbyly jí ale žádné zbraně, tak se vrátila domů."
            return

        if self.args.goal == ArmyGoal.Eliminate:
            equipment = self.map.retreatArmy(attacker)
            self._info += f"Armáda {army.name} vyčistila pole {tile.name} a vrátila se domů"
            self._returnWeaponsInfo(equipment)
            return

        self.map.occupyTile(attacker, tile)
        self._info += f"Armáda {army.name} obsadila pole {tile.name}. Její aktuální síla je {army.strength}"
        return
