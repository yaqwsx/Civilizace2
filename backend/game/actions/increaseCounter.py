from decimal import Decimal
from typing import Optional

from typing_extensions import override

from game.actions.actionBase import TeamActionArgs, TeamInteractionActionBase
from game.entities import RESOURCE_VILLAGER, Resource

# This action is a demonstration of action implementation. Basically you can say
# how much to increase the red Counter. Optionally we can pass an entity (e.g.,
# the player sacrificed to gods) and then it gains some blue counter


class IncreaseCounterArgs(TeamActionArgs):
    red: Decimal
    resource: Optional[Resource] = None


class IncreaseCounterAction(TeamInteractionActionBase):
    # Tady si můžu dodefinovat libovolná pole. Ale měla by mít defaultní hodnotu
    # (aby šel objekt zkonstruovat jen na základě stavu, entit a argumentů)
    # Tato hodnota bude uchována mezi voláními jednotlivých kroků
    extraBlue: int = 42

    @property
    @override
    def args(self) -> IncreaseCounterArgs:
        args = super().args
        assert isinstance(args, IncreaseCounterArgs)
        return args

    @property
    @override
    def description(self) -> str:
        return "Zvýšení počitadla"

    @override
    def cost(self) -> dict[Resource, Decimal]:
        return {}

    @override
    def pointsCost(self) -> int:
        return 20

    @override
    def throwCost(self) -> int:
        return 2 * super().throwCost()  # Házení může pro některou akci stát jinak

    @override
    def _initiateCheck(self) -> None:
        self._ensure(
            self.args.red < 10, "Hráč nemůže zvýšit červené počitado o více než 10"
        )
        self._ensure(self.args.red > -10, "Hráč nemůže snížit počitadlo o více než 10")
        self._ensure(
            self.args.resource is None or self.args.resource.id != RESOURCE_VILLAGER,
            f"Hráči nemohou obětovat lidi - chtěli jste obětovat 1× [[{RESOURCE_VILLAGER}]]",
        )

    @override
    def _commitSuccessImpl(self) -> None:
        teamState = self.team_state()
        self._trace += "Zahájen commit"
        teamState.redCounter += self.args.red
        self._info += f"Týmu bylo zvýšeno červené počítadlo na {teamState.redCounter}"
        self._trace += f"Týmu bylo zvýšeno červené počítadlo na {teamState.redCounter}"

        if self.args.resource is not None:
            teamState.blueCounter += 1
            self._info += (
                f"Týmu bylo zvýšeno modré počítadlo na {teamState.blueCounter}"
            )
