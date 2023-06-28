from decimal import Decimal

from typing_extensions import override

from game.actions.actionBase import TeamActionArgs, TeamInteractionActionBase
from game.util import sum_dict


class FeedArgs(TeamActionArgs):
    pass


class FeedAction(TeamInteractionActionBase):
    @property
    @override
    def args(self) -> FeedArgs:
        args = super().args
        assert isinstance(args, FeedArgs)
        return args

    @property
    @override
    def description(self) -> str:
        return f"Krmení obyvatelstva ({self.args.team.name})"

    @override
    def _initiateCheck(self) -> None:
        self._ensureStrong(
            self.team_state().turn < self.state.world.turn,
            "V tomto kole jste už krmili.",
        )

    @override
    def _commitSuccessImpl(self) -> None:
        raise NotImplementedError()
        req = computeFeedRequirements(self.state, self.entities, self.args.team)
        teamState = self.team_state()

        paid = sum(self.args.materials.values())

        newborns = 0
        if paid >= req.tokensRequired:
            newborns += 10
        else:
            starved = (req.tokensRequired - paid) * 5
            teamState.kill_obyvatels(starved, self.entities)
            self._warnings += f"Chybí {req.tokensRequired - paid} jednotek jídla, uhynulo vám {starved} obyvatel."

        automated = {prod: amount for prod, amount in req.automated}
        saturated = set()
        for resource, amount in self.args.materials.items():
            if amount + automated.get(resource, 0) >= req.tokensPerCaste:
                saturated.add(resource)
        for resource, amount in automated.items():
            if amount >= req.tokensPerCaste:
                saturated.add(resource)

        teamState.add_newborns(newborns, self.entities)

        self._info += (
            f"Krmení úspěšně provedeno. Narodilo se vám {newborns} nových obyvatel."
        )
        self._info += f"Můžete si vzít jeden PUNTÍK NA KOSTKU"

        if self.entities.work not in teamState.resources:
            teamState.resources[self.entities.work] = Decimal(0)

        teamState.resources[self.entities.work] //= 2
        teamState.resources[self.entities.withdraw_capacity] = Decimal(
            self.state.world.withdrawCapacity
        )

        self._receiveResources(
            sum_dict(
                (resource.produces, amount)
                for resource, amount in teamState.resources.items()
                if resource.produces is not None
            )
        )

        teamState.turn = self.state.world.turn
