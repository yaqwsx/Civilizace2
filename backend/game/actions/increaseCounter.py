from decimal import Decimal

from game.actions.actionBase import ActionArgs
from game.actions.actionBase import ActionBase, ActionResult
from game.entities import DieId, Resource, Team
from typing import Iterable, List, Optional, Set, Tuple

# This action is a demonstration of action implementation. Basically you can say
# how much to increase the red Counter. Optionally we can pass an entity (e.g.,
# the player sacrificed to gods) and then it gains some blue counter

class ActionIncreaseCounterArgs(ActionArgs):
    team: Team
    red: Decimal
    resource: Optional[Resource]=None

class ActionIncreaseCounter(ActionBase):
    # Tady si můžu dodefinovat libovolná pole. Ale měla by mít defaultní hodnotu
    # (aby šel objekt zkonstruovat jen na základě stavu, entit a argumentů)
    # Tato hodnota bude uchována mezi voláními jednotlivých kroků
    extraBlue: int = 42

    def cost(self):
        return {}

    @property
    def args(self) -> ActionIncreaseCounterArgs:
        assert isinstance(self._generalArgs, ActionIncreaseCounterArgs)
        return self._generalArgs

    def diceRequirements(self) -> Tuple[Iterable[DieId], int]:
        return ["die-lesy"], 20

    def _initiateImpl(self) -> None:
        self._ensure(self.args.red < 10,
            "Hráč nemůže zvýšit červené počitado o více než 10")
        self._ensure(self.args.red > -10,
            "Hráč nemůže snížit počitadlo o více než 10")
        self._ensure(self.args.resource is None or self.args.resource.id != "mat-clovek",
            "Hráči nemohou obětovat lidi - chtěli jste obětovat 1× [[mat-clovek]]")
        self._makePayment({
            self.entities["res-prace"]: Decimal(10),
            self.entities["mat-drevo"]: Decimal(5)
        })
        self._info.add("Splňujte podmínky pro akci.")

    def _commitImpl(self) -> bool:
        self.teamState.redCounter += self.args.red
        self._info.add(f"Týmu bylo zvýšeno počítadlo na {self.teamState.redCounter}")

        if self.args.resource is not None:
            self.teamState.blueCounter += 1
            self._info.add(f"Týmu bylo zvýšeno počítadlo na {self.teamState.blueCounter}")

        return True # Result was expected


    def requiresDelayedEffect(self) -> int:
        return 0
