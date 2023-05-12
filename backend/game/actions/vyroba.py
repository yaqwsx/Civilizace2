from collections import defaultdict
from decimal import Decimal
from math import ceil, floor
from typing import Dict, Iterable, NamedTuple, Optional, Tuple

from typing_extensions import override

from game.actions.actionBase import (NoInitActionBase, TeamActionArgs,
                                     TeamActionBase, TeamInteractionActionBase,
                                     TileActionArgs)
from game.actions.common import MessageBuilder
from game.entities import Die, Resource, Vyroba
from game.state import printResourceListForMarkdown


class VyrobaArgs(TeamActionArgs, TileActionArgs):
    vyroba: Vyroba
    count: int
    plunder: bool
    genericsMapping: Dict[Resource, Resource] = {}

class VyrobaReward(NamedTuple):
    reward: Dict[Resource, Decimal]
    bonus: Decimal
    plundered: Optional[int]

    def tracked(self) -> Dict[Resource, Decimal]:
        return {reward: amount for reward, amount in self.reward.items() if reward.isTracked}


def computeVyrobaReward(args: VyrobaArgs, tileRichnessTokens: int) -> VyrobaReward:
    resource, amount = args.vyroba.reward
    amount *= args.count

    bonus = Decimal(tileRichnessTokens) / 10
    if args.plunder:
        plundered = min(tileRichnessTokens, args.count)
        tileRichnessTokens -= plundered
    else:
        plundered = None

    reward = {resource: amount * (1 + bonus) + (plundered or 0)}
    return VyrobaReward(reward=reward, bonus=bonus, plundered=plundered)


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
    def cost(self) -> Dict[Resource, Decimal]:
        result: Dict[Resource, Decimal] = defaultdict(Decimal)
        for resource, cost in self.args.vyroba.cost.items():
            if resource in self.args.genericsMapping:
                resource = self.args.genericsMapping[resource]
            result[resource] += cost * self.args.count
        return result

    @override
    def diceRequirements(self) -> Tuple[Iterable[Die], int]:
        points = ceil(self.args.vyroba.points * (1 + self.args.count) / 2)
        return (self.teamState.getUnlockingDice(self.args.vyroba), points)

    def travelTime(self) -> int:
        return ceil(self.state.map.getActualDistance(self.args.team, self.args.tile))

    @override
    def _initiateCheck(self) -> None:
        self._ensureStrong(self.state.map.getOccupyingTeam(self.args.tile) == self.args.team,
                           f"Nelze provést výrobu, protože pole {self.args.tile.name} není v držení týmu.")
        for feature in self.args.vyroba.requiredFeatures:
            self._ensure(feature in self.args.tileState(self.state).features,
                         f"Na poli {self.args.tile.name} chybí {feature.name}")

    @override
    def _commitSuccessImpl(self) -> None:
        if travelTime := self.travelTime() > 0:
            scheduled = self._scheduleAction(VyrobaCompletedAction, self.args, travelTime)
            self._info += f"Zadání výroby bylo úspěšné. Akce se vyhodnotí za {ceil(scheduled.delay_s / 60)} minut"
        else:
            self._info += f"Zadání výroby bylo úspěšné"
            tileState = self.args.tileState(self.state)
            reward = computeVyrobaReward(self.args, tileState.richnessTokens)

            if reward.plundered is not None:
                tileState.richnessTokens -= reward.plundered
                assert tileState.richnessTokens >= 0

            instantReward = self._receiveResources(reward.reward, instantWithdraw=True)
            self._info += f"Dejte týmu materiály:\n\n{printResourceListForMarkdown(instantReward, floor)}"

            if len(tracked := reward.tracked()) > 0:
                self._info += f"Tým obdržel v systému:\n\n{printResourceListForMarkdown(tracked)}"
            if reward.bonus != 0:
                self._info += f"Bonus za úrodnost výroby: {ceil(100 * reward.bonus):+}%"
            if reward.plundered is not None:
                self._info += f"Odebráno {reward.plundered} jednotek úrody"


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
        tileState = self.args.tileState(self.state)
        reward = computeVyrobaReward(self.args, tileState.richnessTokens)

        if reward.plundered is not None:
            tileState.richnessTokens -= reward.plundered
            assert tileState.richnessTokens >= 0

        self._receiveResources(reward.reward)

        if len(tracked := reward.tracked()) > 0:
            self._info += f"Tým obdržel v systému:\n\n{printResourceListForMarkdown(tracked)}"
        if reward.bonus != 0:
            self._info += f"Bonus za úrodnost výroby: {ceil(100 * reward.bonus):+}%"
        if reward.plundered is not None:
            self._info += f"Odebráno {reward.plundered} jednotek úrody"

        msgBuilder = MessageBuilder(message=f"Výroba {self.args.vyroba.name} dokončena:")
        msgBuilder += self._warnings
        msgBuilder += self._info
        self._addNotification(self.args.team, msgBuilder.message)
