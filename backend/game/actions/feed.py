from decimal import Decimal
from math import ceil, floor
from typing import Dict, List, Tuple

from pydantic import BaseModel
from typing_extensions import override

from game.actions.actionBase import TeamActionArgs, TeamInteractionActionBase
from game.entities import Entities, Resource, TeamEntity
from game.state import GameState, TeamState


class FeedRequirements(BaseModel):
    tokensRequired: int
    tokensPerCaste: int
    casteCount: int
    automated: List[Tuple[Resource, int]]  # sorted in preferred display order


def computeFeedRequirements(
    state: GameState, entities: Entities, team: TeamEntity
) -> FeedRequirements:
    teamState = state.teamStates[team]
    tokensRequired = ceil(teamState.population / 20)
    foodPerCaste = ceil(tokensRequired / (2 * state.world.casteCount))

    automated = [
        (production.produces, amount)
        for production, amount in teamState.granary.items()
        if production.produces is not None
    ]
    automatedCount = floor(sum(amount for production, amount in automated))

    return FeedRequirements(
        tokensRequired=max(tokensRequired - automatedCount, 0),
        tokensPerCaste=foodPerCaste,
        casteCount=state.world.casteCount,
        automated=automated,
    )


class FeedArgs(TeamActionArgs):
    materials: Dict[Resource, int]


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
    def cost(self) -> Dict[Resource, int]:
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
            self.teamState.kill_obyvatels(starved)
            self._warnings += f"Chybí {req.tokensRequired - paid} jednotek jídla, uhynulo vám {starved} obyvatel."

        automated = {prod: amount for prod, amount in req.automated}
        saturated = set()
        for resource, amount in self.args.materials.items():
            if amount + automated.get(resource, 0) >= req.tokensPerCaste:
                saturated.add(resource)
        for resource, amount in automated.items():
            if amount >= req.tokensPerCaste:
                saturated.add(resource)

        self.teamState.add_newborns(newborns)

        self._info += (
            f"Krmení úspěšně provedeno. Narodilo se vám {newborns} nových obyvatel."
        )
        self._info += f"Můžete si vzít jeden PUNTÍK NA KOSTKU"

        self.teamState.work //= 2
        self.teamState.withdraw_capacity = Decimal(self.state.world.withdrawCapacity)

        self._receiveResources(
            {
                resource.produces: amount
                for resource, amount in self.teamState.resources.items()
                if resource.produces is not None
            }
        )

        self.teamState.turn = self.state.world.turn
