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

    def _adjustObyvatels(self, diff_amount: int) -> None:
        teamState = self.teamState
        obyvatel = self.entities.obyvatel
        if obyvatel not in teamState.resources:
            teamState.resources[obyvatel] = Decimal(0)
        teamState.resources[obyvatel] += diff_amount
        if teamState.resources[obyvatel] < 0:
            teamState.resources[obyvatel] = Decimal(0)

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
            self._adjustObyvatels(-starved)
            self._warnings += f"Chybí {req.tokensRequired - paid} jednotek jídla, takže uhynulo {starved} obyvatel"

        automated = {prod: amount for prod, amount in req.automated}
        saturated = set()
        for resource, amount in self.args.materials.items():
            if amount + automated.get(resource, 0) >= req.tokensPerCaste:
                saturated.add(resource)
        for resource, amount in automated.items():
            if amount >= req.tokensPerCaste:
                saturated.add(resource)

        self._adjustObyvatels(newborns)

        self._info += (
            f"Krmení úspěšně provedeno. Narodilo se vám {newborns} nových obyvatel."
        )
        self._info += f"Můžete si vzít jeden PUNTÍK NA KOSTKU"

        self.teamState.resources[self.entities.work] = (
            self.teamState.resources.get(self.entities.work, Decimal(0)) // 2
        )

        reward = {
            resource.produces: amount
            for resource, amount in self.teamState.resources.items()
            if resource.produces is not None
        }
        self._receiveResources(reward)

        self.teamState.turn = self.state.world.turn
