from typing_extensions import override

from game.actions.actionBase import TeamActionArgs, TeamInteractionActionBase
from game.state import ArmyMode


class ArmyRetreatArgs(TeamActionArgs):
    armyIndex: int


class ArmyRetreatAction(TeamInteractionActionBase):
    @property
    @override
    def args(self) -> ArmyRetreatArgs:
        args = super().args
        assert isinstance(args, ArmyRetreatArgs)
        return args

    @property
    @override
    def description(self) -> str:
        return f"Stažení armády {self.army_state().name} ({self.args.team.name})"

    @override
    def _initiateCheck(self) -> None:
        army = self.army_state()
        self._ensureStrong(
            army.team == self.args.team, f"Armáda nepatří týmu {self.args.team.name}"
        )
        self._ensureStrong(
            army.mode == ArmyMode.Occupying,
            f"Nelze stáhnout armádu, která nestojí na poli.",
        )
        assert army.tile is not None

    @override
    def _commitSuccessImpl(self) -> None:
        army = self.army_state()
        orig_tile = army.tile
        assert orig_tile is not None
        equipment = army.retreat()

        self._info += f"Armáda {army.name} se stáhla z pole {orig_tile.name}."
        self._info += f"Vydejte týmu [[{self.entities.zbrane}|{equipment}]]."
