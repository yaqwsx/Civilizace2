from decimal import Decimal

from typing_extensions import override

from game.actions.actionBase import TeamActionArgs, TeamInteractionActionBase
from game.actions.vyroba import computeVyrobaReward
from game.entities import Vyroba


class VyrobaRevertArgs(TeamActionArgs):
    vyroba: Vyroba
    count: int


class VyrobaRevertAction(TeamInteractionActionBase):
    @property
    @override
    def args(self) -> VyrobaRevertArgs:
        assert isinstance(self._generalArgs, VyrobaRevertArgs)
        return self._generalArgs

    @property
    @override
    def description(self) -> str:
        return f"Vrácení výroby {self.args.count}× {self.args.vyroba.name} ({self.args.team.name})"

    def getReturnObyvatelCount(self) -> Decimal:
        obyvatel_cost = self.args.vyroba.cost.get(self.entities.obyvatel, Decimal(0))
        return self.args.count * obyvatel_cost

    @override
    def cost(self):
        return computeVyrobaReward(self.args.vyroba, self.args.count, bonus=Decimal(0))

    @override
    def _initiateCheck(self) -> None:
        self._ensureStrong(
            self.args.count > 0, f"Počet výrob na vrácení musí být kladný"
        )
        teamState = self.teamState
        self._ensureStrong(
            self.args.vyroba in teamState.employees,
            f"Tým nemá [[{self.args.vyroba.id}]]",
        )
        self._ensureStrong(
            teamState.employees[self.args.vyroba] >= self.args.count,
            f"Tým má jenom {teamState.employees.get(self.args.vyroba, 0)}× [[{self.args.vyroba.id}]]",
        )

    @override
    def _commitSuccessImpl(self) -> None:
        self.teamState.employees.setdefault(self.args.vyroba, 0)
        self.teamState.employees[self.args.vyroba] -= self.args.count
        assert self.teamState.employees[self.args.vyroba] >= 0
        self._info += f"Obyvatelé přestali být specializovaní: {self.args.count}× [[{self.args.vyroba.id}]]"

        return_obyvatel_count = self.getReturnObyvatelCount()
        self._receiveResources({self.entities.obyvatel: return_obyvatel_count})
        self._info += (
            f"Týmu se vrátilo {return_obyvatel_count}× [[{self.entities.obyvatel.id}]]"
        )
