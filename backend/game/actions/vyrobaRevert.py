from decimal import Decimal
from typing import Tuple

from typing_extensions import override

from game.actions.actionBase import TeamActionArgs, TeamInteractionActionBase
from game.entities import Resource, Vyroba


class VyrobaRevertArgs(TeamActionArgs):
    vyroba: Vyroba
    count: int


class VyrobaRevert(TeamInteractionActionBase):
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

    def getRevertedResources(self) -> Tuple[Resource, Decimal]:
        reward, amount = self.args.vyroba.reward
        return reward, self.args.count * amount

    @override
    def _initiateCheck(self) -> None:
        self._ensureStrong(
            self.args.count > 0, f"Počet výrob na vrácení musí být kladný"
        )
        teamState = self.teamState
        self._ensureStrong(
            self.args.vyroba not in teamState.employees,
            f"Tým nemá [[{self.args.vyroba.id}]]",
        )
        self._ensureStrong(
            teamState.employees[self.args.vyroba] >= self.args.count,
            f"Tým má jenom {teamState.employees.get(self.args.vyroba, 0)}× [[{self.args.vyroba.id}]]",
        )

        revertedRes, revertedAmount = self.getRevertedResources()
        availableAmount = self.teamState.resources.get(revertedRes, 0)
        self._ensureStrong(
            availableAmount >= revertedAmount,
            f"Tým nemá dostatečné zdroje na vrácení {self.args.count}× [[{self.args.vyroba.id}]] (chybí {revertedAmount - availableAmount}× [[{revertedRes.id}]])",
        )

    @override
    def _commitSuccessImpl(self) -> None:
        self.teamState.employees.setdefault(self.args.vyroba, 0)
        self.teamState.employees[self.args.vyroba] -= self.args.count
        assert self.teamState.employees[self.args.vyroba] >= 0
        self._info += f"{self.args.count}× [[{self.args.vyroba.id}]] přestal pracovat"

        revertedRes, revertedAmount = self.getRevertedResources()
        tokens = self._payResources({revertedRes: revertedAmount})
        assert len(tokens) == 0
        self._info += f"Tým přišel o výrobu {revertedAmount}× [[{revertedRes}]]"

        return_obyvatel_count = self.getReturnObyvatelCount()
        self._receiveResources({self.entities.obyvatel: return_obyvatel_count})
        self._info += (
            f"Týmu se vrátilo {return_obyvatel_count}× [[{self.entities.obyvatel.id}]]"
        )
