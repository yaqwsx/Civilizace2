from decimal import Decimal
from math import ceil, floor
from typing import Tuple

from pydantic import BaseModel
from typing_extensions import override

from game.actions.actionBase import TeamActionArgs, TeamInteractionActionBase
from game.entities import Entities, Resource, TeamEntity
from game.state import GameState
from game.util import sum_dict


class FeedRequirements(BaseModel):
    tokensRequired: int
    tokensPerCaste: int
    casteCount: int
    automated: list[Tuple[Resource, int]]  # sorted in preferred display order


def computeFeedRequirements(
    state: GameState, entities: Entities, team: TeamEntity
) -> FeedRequirements:
    teamState = state.teamStates[team]
    tokensRequired = ceil(teamState.population / 20)
    foodPerCaste = ceil(tokensRequired / (2 * state.world.casteCount))

    automated = sorted(
        sum_dict(
            (production.produces, amount)
            for production, amount in teamState.granary.items()
            if production.produces is not None
        ).items(),
        key=lambda res: (res[0].tradable, res[0].name),
    )
    automatedCount = floor(sum(amount for production, amount in automated))

    return FeedRequirements(
        tokensRequired=max(tokensRequired - automatedCount, 0),
        tokensPerCaste=foodPerCaste,
        casteCount=state.world.casteCount,
        automated=automated,
    )


class FeedArgs(TeamActionArgs):
    materials: dict[Resource, int]


class FeedAction(TeamInteractionActionBase):
    @property
    @override
    def args(self) -> FeedArgs:
        assert isinstance(self._generalArgs, FeedArgs)
        return self._generalArgs

    @property
    @override
    def description(self) -> str:
        return f"Krmení obyvatelstva ({self.args.team.name})"

    @override
    def cost(self) -> dict[Resource, int]:
        return self.args.materials

    @override
    def _initiateCheck(self) -> None:
        self._ensureStrong(
            self.teamState.turn < self.state.world.turn, "V tomto kole už jste krmili."
        )

    @override
    def _commitSuccessImpl(self) -> None:
        req = computeFeedRequirements(self.state, self.entities, self.args.team)

        paid = sum(self.args.materials.values())

        newborns = 0
        if paid >= req.tokensRequired:
            newborns += 10
        else:
            starved = (req.tokensRequired - paid) * 5
            self.teamState.kill_obyvatels(starved, self.entities)
            self._warnings += f"Chybí {req.tokensRequired - paid} jednotek jídla, uhynulo vám {starved} obyvatel."

        automated = {prod: amount for prod, amount in req.automated}
        saturated = set()
        for resource, amount in self.args.materials.items():
            if amount + automated.get(resource, 0) >= req.tokensPerCaste:
                saturated.add(resource)
        for resource, amount in automated.items():
            if amount >= req.tokensPerCaste:
                saturated.add(resource)

        self.teamState.add_newborns(newborns, self.entities)

        self._info += (
            f"Krmení úspěšně provedeno. Narodilo se vám {newborns} nových obyvatel."
        )
        self._info += f"Můžete si vzít jeden PUNTÍK NA KOSTKU"

        if self.entities.work not in self.teamState.resources:
            self.teamState.resources[self.entities.work] = Decimal(0)

        self.teamState.resources[self.entities.work] //= 2
        self.teamState.resources[self.entities.withdraw_capacity] = Decimal(
            self.state.world.withdrawCapacity
        )

        self._receiveResources(
            sum_dict(
                (resource.produces, amount)
                for resource, amount in self.teamState.resources.items()
                if resource.produces is not None
            )
        )

        self.teamState.turn = self.state.world.turn
