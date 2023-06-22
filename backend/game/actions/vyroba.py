from decimal import Decimal
from math import ceil, floor
from typing import NamedTuple

from typing_extensions import override

from game import state
from game.actions.actionBase import (
    TeamActionArgs,
    TeamInteractionActionBase,
    TileActionArgs,
)
from game.actions.common import printResourceListForMarkdown
from game.entities import Resource, Vyroba
from game.util import sum_dict


class VyrobaArgs(TeamActionArgs, TileActionArgs):
    vyroba: Vyroba
    count: int


def computeVyrobaReward(
    vyroba: Vyroba, count: int, *, bonus: Decimal
) -> dict[Resource, Decimal]:
    return sum_dict(
        (res, amount * (1 + bonus) * count) for res, amount in vyroba.all_rewards()
    )


class VyrobaAction(TeamInteractionActionBase):
    @property
    @override
    def args(self) -> VyrobaArgs:
        assert isinstance(self._generalArgs, VyrobaArgs)
        return self._generalArgs

    @property
    @override
    def description(self) -> str:
        return f"Výroba {self.args.vyroba.name} ({self.args.vyroba.reward[1]*self.args.count}× {self.args.vyroba.reward[0].name}, {self.args.team.name})"

    @override
    def cost(self) -> dict[Resource, Decimal]:
        return {
            resource: self.args.count * cost
            for resource, cost in self.args.vyroba.cost.items()
        }

    @override
    def pointsCost(self) -> int:
        return ceil(self.args.vyroba.points * (1 + self.args.count) / 2)

    @override
    def _initiateCheck(self) -> None:
        self._ensureStrong(self.args.count > 0, f"Počet výrob musí být kladný")
        self._ensureStrong(
            self.state.map.getOccupyingTeam(self.args.tile, self.state.teamStates)
            == self.args.team,
            f"Nelze provést výrobu, protože pole {self.args.tile.name} není v držení týmu.",
        )
        for feature in self.args.vyroba.requiredTileFeatures:
            self._ensure(
                feature in self.args.tileState(self.state).features,
                f"Na poli {self.args.tile.name} chybí {feature.name}",
            )

    def revertible(self) -> bool:
        reward, amount = self.args.vyroba.reward
        return (
            reward.isTradableProduction
            and self.args.vyroba.cost.get(self.entities.obyvatel, 0) > 0
        )

    @override
    def _commitSuccessImpl(self) -> None:
        self._info += f"Zadání výroby bylo úspěšné."
        bonus = self.args.tileState(self.state).richnessTokens / Decimal(10)
        reward = computeVyrobaReward(self.args.vyroba, self.args.count, bonus=bonus)

        instantReward = self._receiveResources(reward, instantWithdraw=True)
        self._info += printResourceListForMarkdown(
            instantReward,
            floor,
            header="Dejte týmu materiály:",
            emptyHeader="Nedávejte týmu žádné materiály",
        )

        self._info += printResourceListForMarkdown(
            {res: amount for res, amount in reward.items() if not res.isWithdrawable},
            header="Tým obdržel v systému:",
        )
        if bonus != 0:
            self._info += f"Bonus za úrodnost výroby: {ceil(100 * bonus):+}%"

        if self.revertible():
            self.teamState.employees.setdefault(self.args.vyroba, 0)
            self.teamState.employees[self.args.vyroba] += self.args.count
            self._info += f"Tým dostal v systému zaměstnance {self.args.count}× [[{self.args.vyroba.id}]]"
