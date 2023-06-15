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


class VyrobaArgs(TeamActionArgs, TileActionArgs):
    vyroba: Vyroba
    count: int


class VyrobaReward(NamedTuple):
    reward: dict[Resource, Decimal]
    bonus: Decimal

    def tracked(self) -> dict[Resource, Decimal]:
        return {
            reward: amount for reward, amount in self.reward.items() if reward.isTracked
        }


def computeVyrobaReward(args: VyrobaArgs, tileState: state.MapTile) -> VyrobaReward:
    resource, amount = args.vyroba.reward

    bonus = Decimal(tileState.richnessTokens) / 10
    reward = {resource: amount * (1 + bonus) * args.count}
    return VyrobaReward(reward=reward, bonus=bonus)


class VyrobaAction(TeamInteractionActionBase):
    @property
    @override
    def args(self) -> VyrobaArgs:
        assert isinstance(self._generalArgs, VyrobaArgs)
        return self._generalArgs

    @property
    @override
    def description(self) -> str:
        return f"Výroba {self.args.vyroba.reward[1]*self.args.count}× {self.args.vyroba.reward[0].name} ({self.args.team.name})"

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
            reward.isProduction
            and not reward.nontradable
            and self.args.vyroba.cost.get(self.entities.obyvatel, 0) > 0
        )

    @override
    def _commitSuccessImpl(self) -> None:
        self._info += f"Zadání výroby bylo úspěšné."
        reward = computeVyrobaReward(self.args, self.args.tileState(self.state))

        instantReward = self._receiveResources(reward.reward, instantWithdraw=True)
        self._info += printResourceListForMarkdown(
            instantReward,
            floor,
            header="Dejte týmu materiály:",
            emptyHeader="Nedávejte týmu žádné materiály",
        )

        self._info += printResourceListForMarkdown(
            reward.tracked(), header="Tým obdržel v systému:"
        )
        if reward.bonus != 0:
            self._info += f"Bonus za úrodnost výroby: {ceil(100 * reward.bonus):+}%"

        if self.revertible():
            self.teamState.employees.setdefault(self.args.vyroba, 0)
            self.teamState.employees[self.args.vyroba] += self.args.count
            self._info += f"Tým dostal v systému zaměstnance {self.args.count}× [[{self.args.vyroba.id}]]"
