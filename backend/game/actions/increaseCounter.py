from decimal import Decimal
from typing import Dict, Iterable, Optional, Tuple

from typing_extensions import override

from game.actions.actionBase import TeamActionArgs, TeamInteractionActionBase
from game.entities import RESOURCE_VILLAGER, Die, Resource

# This action is a demonstration of action implementation. Basically you can say
# how much to increase the red Counter. Optionally we can pass an entity (e.g.,
# the player sacrificed to gods) and then it gains some blue counter

class IncreaseCounterArgs(TeamActionArgs):
    red: Decimal
    resource: Optional[Resource]=None

class IncreaseCounterAction(TeamInteractionActionBase):
    # Tady si můžu dodefinovat libovolná pole. Ale měla by mít defaultní hodnotu
    # (aby šel objekt zkonstruovat jen na základě stavu, entit a argumentů)
    # Tato hodnota bude uchována mezi voláními jednotlivých kroků
    extraBlue: int = 42

    @property
    @override
    def args(self) -> IncreaseCounterArgs:
        assert isinstance(self._generalArgs, IncreaseCounterArgs)
        return self._generalArgs

    @property
    @override
    def description(self) -> str:
        return "Zvýšení počitadla"

    @override
    def cost(self) -> Dict[Resource, Decimal]:
        return {}

    @override
    def diceRequirements(self) -> Tuple[Iterable[Die], int]:
        return [self.entities.dice["die-lesy"]], 20

    @override
    def throwCost(self) -> int:
        return 2 * super().throwCost()  # Házení může pro některou akci stát jinak

    @override
    def _initiateCheck(self) -> None:
        self._ensure(self.args.red < 10,
            "Hráč nemůže zvýšit červené počitado o více než 10")
        self._ensure(self.args.red > -10,
            "Hráč nemůže snížit počitadlo o více než 10")
        self._ensure(self.args.resource is None or self.args.resource.id != RESOURCE_VILLAGER,
            f"Hráči nemohou obětovat lidi - chtěli jste obětovat 1× [[{RESOURCE_VILLAGER}]]")

    @override
    def _commitSuccessImpl(self) -> None:
        self.trace.add("Zahájen commit")
        self.teamState.redCounter += self.args.red
        self._info.add(f"Týmu bylo zvýšeno červené počítadlo na {self.teamState.redCounter}")
        self.trace.add(f"Týmu bylo zvýšeno červené počítadlo na {self.teamState.redCounter}")

        if self.args.resource is not None:
            self.teamState.blueCounter += 1
            self._info.add(f"Týmu bylo zvýšeno modré počítadlo na {self.teamState.blueCounter}")
