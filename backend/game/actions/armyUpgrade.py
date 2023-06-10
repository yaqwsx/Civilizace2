from decimal import Decimal

from typing_extensions import override

from game.actions.actionBase import TeamActionArgs, TeamInteractionActionBase
from game.entities import Resource
from game.state import Army, ArmyMode


class ArmyUpgradeArgs(TeamActionArgs):
    armyIndex: int


class ArmyUpgradeAction(TeamInteractionActionBase):
    @property
    @override
    def args(self) -> ArmyUpgradeArgs:
        assert isinstance(self._generalArgs, ArmyUpgradeArgs)
        return self._generalArgs

    @property
    @override
    def description(self) -> str:
        return f"Vylepšení armády {self.state.map.armies[self.args.armyIndex]} ({self.args.team.name})"

    @override
    def cost(self) -> dict[Resource, Decimal]:
        army = self.state.map.armies[self.args.armyIndex]
        return self.state.world.armyUpgradeCosts[army.level + 1]

    @property
    def army(self) -> Army:
        return self.state.map.armies[self.args.armyIndex]

    @override
    def _initiateCheck(self) -> None:
        army = self.army
        self._ensureStrong(
            army.team == self.args.team, f"Armáda nepatří týmu {self.args.team.name}"
        )
        self._ensureStrong(
            army.mode == ArmyMode.Idle, "Nelze vylepši armádu, která není doma."
        )
        self._ensureStrong(
            army.level < 3, f"Armáda má už level {army.level}, není možné ji povyýšit"
        )

    @override
    def _commitSuccessImpl(self) -> None:
        army = self.army
        army.level += 1
        self._info += f"Armáda {army.name} byla vylepšena na úroveň {army.level}"
