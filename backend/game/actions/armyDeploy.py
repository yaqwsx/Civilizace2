from math import floor
from typing import Optional

from typing_extensions import override

from game.actions.actionBase import (
    NoInitActionBase,
    TeamActionArgs,
    TeamInteractionActionBase,
)
from game.entities import MapTileEntity, Resource, TeamEntity
from game.state import Army, ArmyGoal, ArmyMode


class ArmyDeployArgs(TeamActionArgs):
    tile: MapTileEntity
    armyIndex: int
    goal: ArmyGoal
    equipment: int
    # Support mode allows chosing a team to support; should be defaulted to the team currently occupying target tile
    friendlyTeam: Optional[TeamEntity]


class ArmyDeployAction(TeamInteractionActionBase):
    @property
    @override
    def args(self) -> ArmyDeployArgs:
        args = super().args
        assert isinstance(args, ArmyDeployArgs)
        return args

    @property
    @override
    def description(self) -> str:
        return f"Vyslání armády {self.army_state().name} na pole {self.args.tile.name} ({self.args.team.name})"

    @override
    def cost(self) -> dict[Resource, int]:
        army = self.army_state()
        self._ensureStrong(
            army.capacity >= self.args.equipment,
            f"Kapacita armády je {army.capacity}",
        )
        self._ensureStrong(self.args.equipment > 0, f"Nelze vyslat nevybavenou armádu")
        return {self.entities.zbrane: self.args.equipment}

    def travelTime(self) -> int:
        return self.state.map.getActualDistance(
            self.args.team, self.args.tile, self.state.teamStates
        )

    @override
    def _initiateCheck(self) -> None:
        army = self.army_state()

        self._ensureStrong(
            army.team == self.args.team, f"Nelze vyslat armádu cizího týmu."
        )
        self._ensureStrong(
            self.args.tile != self.state.map.getHomeOfTeam(self.args.team).entity,
            f"Nelze pochodovat na vlastní domovské pole.",
        )

        self._ensureStrong(
            army.mode == ArmyMode.Idle,
            f"Armáda {army.name} už je vyslána na pole {army.tile.name if army.tile is not None else ''}.",
        )

        self._ensureStrong(
            self.args.equipment >= 1,
            f"Nelze poskytnout nekladný počet zbraní ({self.args.equipment}). Minimální počet je 1.",
        )
        self._ensureStrong(
            self.args.equipment <= army.capacity,
            f"Armáda neunese {self.args.equipment} zbraní. Maximální možná výzbroj je {army.capacity}.",
        )

    @override
    def _commitSuccessImpl(self) -> None:
        army = self.army_state()

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

        self._scheduleAction(
            ArmyArrivalAction, args=self.args, delay_s=self.travelTime()
        )


class ArmyArrivalAction(NoInitActionBase):
    @property
    @override
    def args(self) -> ArmyDeployArgs:
        args = super().args
        assert isinstance(args, ArmyDeployArgs)
        return args

    @property
    @override
    def description(self) -> str:
        return f"Příchod armády {self.army_state().name} na pole {self.args.tile.name} ({self.args.team.name})"

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
        army = self.army_state()
        defender = self.state.map.getOccupyingArmy(
            self.args.tile, self.state.teamStates
        )

        if defender == None:
            if self.args.goal != ArmyGoal.Occupy and self.args.goal != ArmyGoal.Replace:
                equipment = army.retreat()
                self._info += f"Pole {self.args.tile.name} je prázdné, armáda {army.name} se vrátila zpět"
                self._returnWeaponsInfo(equipment)
                return
            else:
                army.occupyTile(self.args.tile)
                self._info += f"Armáda {army.name} obsadila pole {self.args.tile.name}"
                return

        if defender.team == army.team:
            if self.args.goal == ArmyGoal.Eliminate:
                equipment = army.retreat()
                self._info += f"Pole {self.args.tile.name} už bylo obsazeno vaší armádou {defender.name}. \
                    Armáda {army.name} se vrátila domů."
                self._returnWeaponsInfo(equipment)
                return

            provider = defender if self.args.goal == ArmyGoal.Replace else army
            receiver = army if self.args.goal == ArmyGoal.Replace else defender
            transfered = self.transferEquipment(provider, receiver)
            if self.args.goal == ArmyGoal.Replace:
                army.boost = defender.boost

            equipment = provider.retreat()
            if self.args.goal == ArmyGoal.Replace:
                receiver.occupyTile(self.args.tile)

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
            equipment = army.retreat()

            self._info += f"Armáda {army.name} posílila armádu týmu [[{self.args.friendlyTeam}]] o {transfered} zbraní."
            self._returnWeaponsInfo(equipment)

            self._addNotification(
                defender.team,
                f"Tým [[{army.team}]] posílil vaši armádu {defender.name} na poli {self.args.tile.name} o {transfered} zbraní.\n\
                Nová síla armády {defender.name} je {defender.strength}.",
            )
            return

        if self.args.goal == ArmyGoal.Supply:
            equipment = army.retreat()
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
            equipment = army.retreat()
            self._returnWeaponsInfo(equipment)

            if defender.equipment == 0:
                defender.retreat()
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

        defenderReward = defender.retreat()
        self._addNotification(
            defender.team,
            f"Armáda {defender.name} byla poražena na poli {self.args.tile.name} a vrátila se domů."
            + f" Do skladu vám bylo uloženo {defenderReward} zbraní, které jí po souboji zůstaly"
            if defenderReward > 0
            else "",
        )

        if army.equipment == 0:
            army.retreat()
            self._info += f"Armáda {army.name} dobyla pole {self.args.tile.name}. Nezbyly jí ale žádné zbraně, tak se vrátila domů."
            return

        if self.args.goal == ArmyGoal.Eliminate:
            equipment = attacker.retreat()
            self._info += f"Armáda {army.name} vyčistila pole {self.args.tile.name} a vrátila se domů"
            self._returnWeaponsInfo(equipment)
            return

        attacker.occupyTile(self.args.tile)
        self._info += f"Armáda {army.name} obsadila pole {self.args.tile.name}. Její aktuální síla je {army.strength}"
        return
