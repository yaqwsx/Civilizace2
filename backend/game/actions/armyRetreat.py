from typing_extensions import override

from game.actions.actionBase import TeamActionArgs, TeamInteractionActionBase
from game.state import Army, ArmyMode


class ArmyRetreatArgs(TeamActionArgs):
    armyIndex: int


class ArmyRetreatAction(TeamInteractionActionBase):
    @property
    @override
    def args(self) -> ArmyRetreatArgs:
        assert isinstance(self._generalArgs, ArmyRetreatArgs)
        return self._generalArgs

    @property
    @override
    def description(self) -> str:
        return f"Stažení armády {self.state.map.armies[self.args.armyIndex]} ({self.args.team.name})"

    @property
    def army(self) -> Army:
        self._ensureStrong(self.args.armyIndex in range(0, len(self.state.map.armies)),
                           f"Neznámá armáda (index: {self.args.armyIndex})")
        return self.state.map.armies[self.args.armyIndex]

    @override
    def _initiateCheck(self) -> None:
        army = self.army
        self._ensureStrong(army.team == self.args.team,
                           f"Armáda nepatří týmu {self.args.team.name}")
        self._ensureStrong(army.mode == ArmyMode.Occupying,
                           f"Nelze stáhnout armádu, která nestojí na poli.")
        assert army.tile is not None

    @override
    def _commitSuccessImpl(self) -> None:
        army = self.army
        orig_tile = army.tile
        assert orig_tile is not None
        equipment = self.state.map.retreatArmy(army)

        self._info += f"Armáda {army.name} se stáhla z pole {orig_tile.name}."
        self._info += f"Vydejte týmu [[{self.entities.zbrane}|{equipment}]]."
