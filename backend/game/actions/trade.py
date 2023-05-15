from decimal import Decimal
from typing import Dict, List

from typing_extensions import override

from game.actions.actionBase import TeamActionArgs, TeamInteractionActionBase
from game.entities import Resource, Team
from game.state import printResourceListForMarkdown


class TradeArgs(TeamActionArgs):
    receiver: Team
    resources: Dict[Resource, Decimal]


class TradeAction(TeamInteractionActionBase):
    @property
    @override
    def args(self) -> TradeArgs:
        assert isinstance(self._generalArgs, TradeArgs)
        return self._generalArgs

    @property
    @override
    def description(self) -> str:
        return f"Prodej produkce týmu {self.args.receiver.name} ({self.args.team.name})"

    @override
    def cost(self) -> Dict[Resource, Decimal]:
        amount = sum(self.args.resources.values(), Decimal(0))
        return {self.entities.resources['mge-obchod']: amount}

    def getNontradable(self) -> List[Resource]:
        return [self.entities.work, self.entities.obyvatel, self.entities.culture]

    @override
    def _initiateCheck(self) -> None:
        self._ensure(self.args.receiver != self.args.team, "Nelze obchodovat sám se sebou")
        self._ensure(len(self.args.resources) > 0, "Není vybráno co obchodovat")

        with self._errors.startList("Obchod nelze provést") as err:
            teamState = self.teamState
            nontradable = self.getNontradable()
            for resource, amount in self.args.resources.items():
                if not resource.isProduction or resource in nontradable:
                    err(f"Nelze obchodovat [[{resource.id}]]")
                    continue

                if amount < 0:
                    err(
                        f"Nelze obchodovat záporné množství {amount}×[[{resource.id}]]")
                    continue

                available = teamState.resources.get(resource, Decimal(0))
                if amount > available:
                    err(
                        f"Tým {self.args.team.name} nemá dostatek [[{resource.id}]] (dostupné: {available}, požadováno: {amount})")
                    continue

    @override
    def _commitSuccessImpl(self) -> None:
        teamState = self.teamState

        for resource, amount in self.args.resources.items():
            them = self.state.teamStates[self.args.receiver]

            if resource not in teamState.resources:
                teamState.resources[resource] = Decimal(0)
            if resource not in them.resources:
                them.resources[resource] = Decimal(0)

            teamState.resources[resource] -= amount
            them.resources[resource] += amount

            assert amount >= 0
            assert teamState.resources[resource] >= 0

        self._info += f"Úspěšně prodáno týmu {self.args.receiver.name}:"
        self._info += printResourceListForMarkdown(self.args.resources)
        self._addNotification(self.args.receiver,
                              f"Od týmu {self.args.team.name} jste dostali {printResourceListForMarkdown(self.args.resources)}")
