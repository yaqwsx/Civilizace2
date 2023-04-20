from decimal import Decimal
from math import ceil, floor
from typing import Dict, Iterable, List, Optional, Set, Tuple
from game.actions.actionBase import ActionArgs, ActionBase
from game.actions.common import ActionFailed
from game.entities import Die, MapTileEntity, NaturalResource, Resource, Team, Vyroba
from game.state import ArmyGoal, printResourceListForMarkdown


class ActionVyrobaArgs(ActionArgs):
    team: Team
    vyroba: Vyroba
    count: int
    tile: MapTileEntity
    plunder: bool
    genericsMapping: Dict[Resource, Resource] = {}

    armyIndex: Optional[int]
    goal: Optional[ArmyGoal]
    equipment: Optional[int]


class ActionVyroba(ActionBase):

    @property
    def args(self) -> ActionVyrobaArgs:
        assert isinstance(self._generalArgs, ActionVyrobaArgs)
        return self._generalArgs

    @property
    def description(self):
        return f"Výroba {self.args.vyroba.reward[1]*self.args.count}× {self.args.vyroba.reward[0].name} ({self.args.team.name})"

    def cost(self) -> Dict[Resource, Decimal]:
        return {resource: cost*self.args.count for resource, cost in self.args.vyroba.cost.items()}

    def diceRequirements(self) -> Tuple[Iterable[Die], int]:
        assert self.teamState is not None
        points = (self.args.vyroba.points * (1 + self.args.count))
        return (self.teamState.getUnlockingDice(self.args.vyroba), ceil(points / 2))

    def requiresDelayedEffect(self) -> Decimal:
        return self.state.map.getActualDistance(self.args.team, self.args.tile)

    def _commitImpl(self) -> None:
        tile = self.tileState
        vyroba = self.args.vyroba
        if self.state.map.getOccupyingTeam(self.args.tile) != self.team:
            raise ActionFailed(
                f"Nelze provést výrobu, protože pole {self.args.tile.name} není v držení týmu.")
        for f in vyroba.requiredFeatures:
            if not isinstance(f, NaturalResource):
                continue
            self._ensure(f in tile.features,
                         f"Na poli {tile.name} chybí {f.name}")
        self._ensureValid()

        self._info += f"Zadání výroby bylo úspěšné. Akce se vyhodnotí za {ceil(self.requiresDelayedEffect() / 60)} minut"

    def _applyDelayedReward(self) -> None:
        self._setupPrivateAttrs()
        reward = self.args.vyroba.reward
        resource = reward[0]
        amount = reward[1] * self.args.count

        multiplier = 1
        plundered = 0

        tile = self.tileState
        multiplier = 1 + (tile.richnessTokens/Decimal(10))
        if self.args.plunder:
            plundered = min(tile.richnessTokens, self.args.count)
            tile.richnessTokens -= plundered

        reward = {resource: amount*multiplier + plundered}

        tokens = self.receiveResources(reward, instantWithdraw=True)

        prods = {r: a for r, a in reward.items() if r.isTracked}
        if prods != {}:
            self._info += f"Tým obdržel v systému:\n\n{printResourceListForMarkdown(prods)}"
        if multiplier > 1:
            self._info += f"Bonus za úrodnost výroby: +{ceil((multiplier-1)*100)}%"
        if plundered > 0:
            self._info += f"Odebráno {plundered} jednotek úrody"
        if tokens != {}:
            self._info += f"Vydejte týmu:\n\n{printResourceListForMarkdown(tokens, floor)}"
        if self.args.vyroba.id == "vyr-koloRezerva":
            self._info += "Oznamte týmu, že VŮZ JE OPRAVEN a popřejte jim ŠŤASTNOU CESTU!"
