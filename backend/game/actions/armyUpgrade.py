from typing import Dict
from game.actions.actionBase import ActionArgs, ActionBase, ActionFailed, HealthyAction
from game.entities import Resource, Team, Tech
from game.state import ArmyMode

class ActionArmyUpgradeArgs(ActionArgs):
    team: Team
    armyIndex: int

class ActionArmyUpgrade(HealthyAction):
    @property
    def args(self) -> ActionArmyUpgradeArgs:
        assert isinstance(self._generalArgs, ActionArmyUpgradeArgs)
        return self._generalArgs

    @property
    def description(self):
        return f"Vylepšení armády {self.state.map.armies[self.args.armyIndex]} ({self.args.team.name})"

    def cost(self) -> Dict[Resource, int]:
        return {}

    def _commitImpl(self) -> None:
        army = self.state.map.armies[self.args.armyIndex]

        if army.team != self.args.team:
            raise ActionFailed(f"Armáda nepatří týmu {self.args.team.name}")

        if army.mode != ArmyMode.Idle:
            raise ActionFailed(f"Nelze vylepši armádu, která není doma.")

        if army.level == 3:
            raise ActionFailed(f"Armáda má už level 3, není možné ji povyýšit")

        army.level += 1

        self._info += f"Armáda {army.name} byla vylepšena na úroveň {army.level}"
