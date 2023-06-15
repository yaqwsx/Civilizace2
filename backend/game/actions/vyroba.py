from decimal import Decimal
from math import ceil, floor
from typing import NamedTuple, Optional

from typing_extensions import override

from game import state
from game.actions.actionBase import (
    NoInitActionBase,
    TeamActionArgs,
    TeamActionBase,
    TeamInteractionActionBase,
    TileActionArgs,
)
from game.actions.common import MessageBuilder, printResourceListForMarkdown
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

    def travelTime(self) -> int:
        return ceil(
            self.state.map.getActualDistance(
                self.args.team, self.args.tile, self.state.teamStates
            )
        )

    @override
    def _initiateCheck(self) -> None:
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

    @override
    def _commitSuccessImpl(self) -> None:
        if travelTime := self.travelTime() > 0:
            scheduled = self._scheduleAction(
                VyrobaCompletedAction, self.args, travelTime
            )
            self._info += f"Zadání výroby bylo úspěšné. Akce se vyhodnotí za {ceil(scheduled.delay_s / 60)} minut."
        else:
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


class VyrobaCompletedAction(TeamActionBase, NoInitActionBase):
    @property
    @override
    def args(self) -> VyrobaArgs:
        assert isinstance(self._generalArgs, VyrobaArgs)
        return self._generalArgs

    @property
    @override
    def description(self) -> str:
        return f"Dokončení výroby {self.args.vyroba.name} na poli {self.args.tile.name} ({self.args.team.name})"

    @override
    def _commitImpl(self) -> None:
        reward = computeVyrobaReward(self.args, self.args.tileState(self.state))

        self._receiveResources(reward.reward)

        self._info += printResourceListForMarkdown(
            reward.reward,
            header="Obdrželi jste v systému:",
            emptyHeader="Neobdrželi jste žádné materiály",
        )
        if reward.bonus != 0:
            self._info += f"Bonus za úrodnost výroby: {ceil(100 * reward.bonus):+}%"

        msgBuilder = MessageBuilder()
        if not self._warnings.empty:
            msgBuilder += f"Výroba [[{self.args.vyroba.id}]] na poli [[{self.args.tile.id}]] se nezdařila:"
            msgBuilder += self._warnings

        msgBuilder += self._info
        self._addNotification(self.args.team, msgBuilder.message)
