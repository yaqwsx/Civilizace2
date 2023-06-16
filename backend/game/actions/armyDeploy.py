from decimal import Decimal
from math import floor
from typing import Optional

from typing_extensions import override

from game.actions.actionBase import (
    NoInitActionBase,
    ScheduledAction,
    TeamActionArgs,
    TeamActionBase,
    TeamInteractionActionBase,
    TileActionArgs,
)
from game.actions.common import ActionFailed
from game.entities import Resource, TeamEntity
from game.state import Army, ArmyGoal, ArmyMode


class ArmyDeployArgs(TeamActionArgs, TileActionArgs):
    armyIndex: int
    goal: ArmyGoal
    equipment: int
    # Support mode allows chosing a team to support; should be defaulted to the team currently occupying target tile
    friendlyTeam: Optional[TeamEntity]


class ArmyDeployAction(TeamInteractionActionBase):
    @property
    @override
    def args(self) -> ArmyDeployArgs:
        assert isinstance(self._generalArgs, ArmyDeployArgs)
        return self._generalArgs

    @property
    @override
    def description(self) -> str:
        return f"Vyslání armády {self.army.name} na pole {self.args.tile.name} ({self.args.team.name})"

    @override
    def cost(self) -> dict[Resource, int]:
        self._ensureStrong(
            self.army.capacity >= self.args.equipment,
            f"Kapacita armády je {self.army.capacity}",
        )
        self._ensureStrong(self.args.equipment > 0, f"Nelze vyslat nevybavenou armádu")
        return {self.entities.zbrane: self.args.equipment}

    @property
    def army(self) -> Army:
        self._ensureStrong(
            self.args.armyIndex in range(0, len(self.state.map.armies)),
            f"Neznámá armáda (index: {self.args.armyIndex})",
        )
        return self.state.map.armies[self.args.armyIndex]

    def travelTime(self) -> Decimal:
        return self.state.map.getActualDistance(
            self.army.team, self.args.tile, self.state.teamStates
        )

    @override
    def _commitSuccessImpl(self) -> None:
        army = self.army
        self._ensureStrong(
            army.team == self.args.team, f"Nelze vyslat armádu cizího týmu."
        )
        self._ensureStrong(
            self.args.tile != self.state.map.getHomeOfTeam(self.args.team).entity,
            f"Nelze útočit na vlastní domovské pole.",
        )

        if army.mode != ArmyMode.Idle:
            assert army.tile is not None, f"Army {army} is in inconsistent state"
            raise ActionFailed(
                f"Armáda {army.name} už je vyslána na pole {army.tile.name}."
            )

        self._ensureStrong(
            self.args.equipment >= 1,
            f"Nelze poskytnout nekladný počet zbraní ({self.args.equipment}). Minimální počet je 1.",
        )
        self._ensureStrong(
            self.args.equipment <= army.capacity,
            f"Armáda neunese {self.args.equipment} zbraní. Maximální možná výzbroj je {army.capacity}.",
        )

        army.tile = self.args.tile
        army.equipment = self.args.equipment
        army.mode = ArmyMode.Marching
        army.goal = self.args.goal

        self._info += (
            f"Armáda [[{army.name}]] vyslána na pole [[{self.args.tile.name}]]"
        )

        defender = self.state.map.getOccupyingTeam(
            self.args.tile, self.state.teamStates
        )
        if defender is not None and defender != self.args.team:
            self._addNotification(
                defender,
                f"Na pole {self.args.tile.name} se blíží cizí armáda. Dorazí za {floor(self.travelTime()/60)} minut",
            )

    def armyArrival(self, delay_s: int) -> ScheduledAction:
        return ScheduledAction(ArmyArrivalAction, args=self.args, delay_s=delay_s)


class ArmyArrivalAction(NoInitActionBase, TeamActionBase):
    @property
    @override
    def args(self) -> ArmyDeployArgs:
        assert isinstance(self._generalArgs, ArmyDeployArgs)
        return self._generalArgs

    @property
    @override
    def description(self) -> str:
        return f"Příchod armády {self.army.name} na pole {self.args.tile.name} ({self.args.team.name})"

    @property
    def army(self) -> Army:
        self._ensureStrong(
            self.args.armyIndex in range(0, len(self.state.map.armies)),
            f"Neznámá armáda (index: {self.args.armyIndex})",
        )
        return self.state.map.armies[self.args.armyIndex]

    @staticmethod
    def transferEquipment(provider: Army, receiver: Army) -> int:
        amount = min(receiver.capacity - receiver.equipment, provider.equipment)
        provider.equipment -= amount
        receiver.equipment += amount
        return amount

    def _returnWeaponsInfo(self, amount: int) -> None:
        self._info += f"Vydejte týmu [[{self.entities.zbrane}|{amount}]]"

    @override
    def _commitImpl(self) -> None:
        army = self.army
        defender = self.state.map.getOccupyingArmy(self.args.tile)

        if defender == None:
            if self.args.goal != ArmyGoal.Occupy and self.args.goal != ArmyGoal.Replace:
                equipment = self.state.map.retreatArmy(army)
                self._info += f"Pole {self.args.tile.name} je prázdné, armáda {army.name} se vrátila zpět"
                self._returnWeaponsInfo(equipment)
                return
            else:
                self.state.map.occupyTile(army, self.args.tileState(self.state))
                self._info += f"Armáda {army.name} obsadila pole {self.args.tile.name}"
                return

        if defender.team == army.team:
            if self.args.goal == ArmyGoal.Eliminate:
                equipment = self.state.map.retreatArmy(army)
                self._info += f"Pole {self.args.tile.name} už bylo obsazeno vaší armádou {defender.name}. \
                    Armáda {army.name} se vrátila domů."
                self._returnWeaponsInfo(equipment)
                return

            provider = defender if self.args.goal == ArmyGoal.Replace else army
            receiver = army if self.args.goal == ArmyGoal.Replace else defender
            transfered = self.transferEquipment(provider, receiver)
            if self.args.goal == ArmyGoal.Replace:
                army.boost = defender.boost

            equipment = self.state.map.retreatArmy(provider)
            if self.args.goal == ArmyGoal.Replace:
                self.state.map.occupyTile(receiver, self.args.tileState(self.state))

            if self.args.goal == ArmyGoal.Replace:
                self._info += f"Armáda {army.name} nahradila předchozí armádu.\
                    Její nová síla je {army.strength}.\
                    Armáda {defender.name} se vrátila domů."
            else:
                self._info += f"Armáda {provider.name} posílila armádu {receiver.name} a vrátila se zpět.\
                Nová síla bránící armády je {receiver.strength}."
            self._returnWeaponsInfo(equipment)
            return

        if (
            self.args.goal == ArmyGoal.Supply
            and self.args.friendlyTeam == defender.team
        ):
            transfered = self.transferEquipment(army, defender)
            equipment = self.state.map.retreatArmy(army)

            self._info += f"Armáda {army.name} posílila armádu týmu [[{self.args.friendlyTeam}]] o {transfered} zbraní."
            self._returnWeaponsInfo(equipment)

            self._addNotification(
                defender.team,
                f"Tým [[{army.team}]] posílil vaši armádu {defender.name} na poli {self.args.tile.name} o {transfered} zbraní.\n\
                Nová síla armády {defender.name} je {defender.strength}.",
            )
            return

        if self.args.goal == ArmyGoal.Supply:
            equipment = self.state.map.retreatArmy(army)
            self._warnings += f"Pole {self.args.tile.name} je obsazeno nepřátelksou armádou. Vaše armáda {army.name} se vrátila domů."
            self._returnWeaponsInfo(equipment)
            return

        attacker = army

        # battle
        defenderCasualties = floor(attacker.strength / 2)
        attackerCasualties = floor(defender.strength / 2)

        defenderLoss = defender.destroyEquipment(defenderCasualties)
        attackertLoss = attacker.destroyEquipment(attackerCasualties)

        # resolve
        if defender.strength >= attacker.strength:
            self._warnings += f"Armáda {army.name} neuspěla v dobývání pole {self.args.tile.name} a vrátila se domů."
            self._returnWeaponsInfo(self.state.map.retreatArmy(army))

            if defender.equipment == 0:
                self.state.map.retreatArmy(defender)
                self._addNotification(
                    defender.team,
                    f"Armáda {defender.name} ubránila pole {self.args.tile.name}, ale utrpěla vysoké ztráty a vrátila se domů.",
                )
            else:
                self._addNotification(
                    defender.team,
                    f"Armáda {defender.name} ubránila pole {self.args.tile.name}. Zbylo jí {defender.equipment} zbraní.",
                )
            return

        defenderReward = self.state.map.retreatArmy(defender)
        self._addNotification(
            defender.team,
            f"Armáda {defender.name} byla poražena na poli {self.args.tile.name} a vrátila se domů."
            + f" Do skladu vám bylo uloženo {defenderReward} zbraní, které jí po souboji zůstaly"
            if defenderReward > 0
            else "",
        )

        if army.equipment == 0:
            self.state.map.retreatArmy(army)
            self._info += f"Armáda {army.name} dobyla pole {self.args.tile.name}. Nezbyly jí ale žádné zbraně, tak se vrátila domů."
            return

        if self.args.goal == ArmyGoal.Eliminate:
            equipment = self.state.map.retreatArmy(attacker)
            self._info += f"Armáda {army.name} vyčistila pole {self.args.tile.name} a vrátila se domů"
            self._returnWeaponsInfo(equipment)
            return

        self.state.map.occupyTile(attacker, self.args.tileState(self.state))
        self._info += f"Armáda {army.name} obsadila pole {self.args.tile.name}. Její aktuální síla je {army.strength}"
        return
