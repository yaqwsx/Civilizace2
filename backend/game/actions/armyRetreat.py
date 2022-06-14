from typing import Dict
from game.actions.actionBase import ActionArgs, ActionBase, ActionFailed, HealthyAction
from game.entities import Resource, Team, Tech
from game.state import ArmyMode

class ActionArmyRetreatArgs(ActionArgs):
    team: Team
    armyIndex: int

class ActionArmyRetreat(HealthyAction):
    @property
    def args(self) -> ActionArmyRetreatArgs:
        assert isinstance(self._generalArgs, ActionArmyRetreatArgs)
        return self._generalArgs

    @property
    def description(self):
        return f"Stažení armády {self.state.map.armies[self.args.armyIndex]} ({self.args.team.name})"

    def cost(self) -> Dict[Resource, int]:
        return {}

    def _commitImpl(self) -> None:
        army = self.state.map.armies[self.args.armyIndex]

        if army.team != self.args.team:
            raise ActionFailed(f"Armáda nepatří týmu {self.args.team.name}")

        if army.mode != ArmyMode.Occupying:
            raise ActionFailed(f"Nelze stáhnout armádu, která nestojí na poli.")

        tile = army.tile
        equipment = self.state.map.retreatArmy(army)

        self._info += f"Armáda {army.name} se stáhla z pole {tile.name}."
        self._info += f"Vydejte týmu [[{self.entities.zbrane}|{equipment}]]."
