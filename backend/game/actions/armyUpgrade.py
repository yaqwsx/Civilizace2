from typing import Dict
from game.actions.actionBase import ActionArgs, ActionBase, ActionFailed, ActionResult, HealthyAction
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

    def applyInitiate(self) -> ActionResult:
        army = self.state.map.armies[self.args.armyIndex]
        if army.team != self.args.team:
            raise ActionFailed(f"Armáda nepatří týmu {self.args.team.name}")
        if army.mode != ArmyMode.Idle:
            raise ActionFailed(f"Nelze vylepši armádu, která není doma.")
        if army.level == 3:
            raise ActionFailed(f"Armáda má už level 3, není možné ji povyýšit")
        # We have to check for the army level before cost. This is why it is
        # necessary to validate in initiate. Not in commit! However, the current
        # implementation of applyInitiate doesn't allow for it, so we have to
        # override. It is quirky, but there is no other way at the moment...
        return super().applyInitiate()

    def cost(self) -> Dict[Resource, int]:
        army = self.state.map.armies[self.args.armyIndex]
        return self.state.world.armyUpgradeCosts[army.level + 1]

    def _commitImpl(self) -> None:
        army = self.state.map.armies[self.args.armyIndex]

        army.level += 1

        self._info += f"Armáda {army.name} byla vylepšena na úroveň {army.level}"
