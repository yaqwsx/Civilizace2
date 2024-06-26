from decimal import Decimal

from typing_extensions import override

from game.actions.actionBase import TeamActionArgs, TeamInteractionActionBase
from game.actions.common import MessageBuilder, printResourceListForMarkdown
from game.entities import Resource, TeamEntity


class TradeArgs(TeamActionArgs):
    receiver: TeamEntity
    resources: dict[Resource, Decimal]


class TradeAction(TeamInteractionActionBase):
    @property
    @override
    def args(self) -> TradeArgs:
        args = super().args
        assert isinstance(args, TradeArgs)
        return args

    @property
    @override
    def description(self) -> str:
        return f"Prodej produkce týmu {self.args.receiver.name} ({self.args.team.name})"

    @override
    def cost(self) -> dict[Resource, Decimal]:
        amount = sum(self.args.resources.values(), Decimal(0))
        return {self.entities.resources["mge-obchod"]: amount}

    @override
    def _initiateCheck(self) -> None:
        self._ensure(
            self.args.receiver != self.args.team, "Nelze obchodovat sám se sebou"
        )
        self._ensure(len(self.args.resources) > 0, "Není vybráno co obchodovat")

        with self._errors.startList("Obchod nelze provést") as err:
            teamState = self.team_state()
            for resource, amount in self.args.resources.items():
                if not resource.isTradableProduction:
                    err(f"Nelze obchodovat [[{resource.id}]]")
                    continue

                if amount < 0:
                    err(f"Nelze obchodovat záporné množství {amount}×[[{resource.id}]]")
                    continue

                available = teamState.resources.get(resource, Decimal(0))
                if amount > available:
                    err(
                        f"Tým {self.args.team.name} nemá dostatek [[{resource.id}]] (dostupné: {available}, požadováno: {amount})"
                    )
                    continue

    @override
    def _commitSuccessImpl(self) -> None:
        receivingTeamState = self.state.teamStates[self.args.receiver]

        self._payResources(self.args.resources)
        for resource, amount in self.args.resources.items():
            assert amount >= 0
            if resource not in receivingTeamState.resources:
                receivingTeamState.resources[resource] = Decimal(0)
            receivingTeamState.resources[resource] += amount

        self._info += f"Úspěšně prodáno týmu {self.args.receiver.name}:"
        self._info += printResourceListForMarkdown(self.args.resources)
        self._addNotification(
            self.args.receiver,
            MessageBuilder(
                f"Od týmu {self.args.team.name} jste dostali:",
                printResourceListForMarkdown(self.args.resources),
            ).message,
        )
