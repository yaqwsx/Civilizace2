from __future__ import annotations

from decimal import Decimal
import math
from typing import Dict, List, Tuple
from game.actions.actionBase import ActionArgs, ActionResult
from game.actions.actionBase import ActionBase
from game.actions.common import ActionFailed
from game.entities import Resource, Team
from game.plague import simulatePlague
from game.state import PlagueStats

class ActionPlagueSentenceArgs(ActionArgs):
    team: Team
    words: List[str]

class ActionPlagueSentence(ActionBase):
    @property
    def args(self) -> ActionPlagueSentenceArgs:
        assert isinstance(self._generalArgs, ActionPlagueSentenceArgs)
        return self._generalArgs

    def cost(self) -> Dict[Resource, Decimal]:
        return {}

    def applyInitiate(self) -> ActionResult:
        tState = self.teamState
        if tState.plague is None:
            raise ActionFailed(f"Nemůžete zadávat věty. Zeptej se na to Honzy.")

        return super().applyInitiate()

    @property
    def description(self):
        return f"Zadávání morové věty pro {self.args.team.name}"


    def _commitImpl(self) -> None:
        plagueData = self.entities.plague
        tState = self.teamState

        sentence = plagueData.getMatchingSentence(self.args.words)
        if sentence is None:
            tState.plague.mortality += 0.01
            self._warnings.add(f"Zadaný recept je neplatný. Uškodili jste svým lidem. Smrtnost se zvýšila na {tState.plague.mortality * 100:.2f}%")
            return

        wordSentence = " ".join([x.word for x in sentence.words])
        if wordSentence in tState.plague.recipes:
            self._warnings.add(f"Zadaný recept byl již použit. Nic se nestalo.")
            return

        tState.plague.recipes.append(wordSentence)
        tState.plague.recovery += sentence.recoveryDiff
        tState.plague.mortality += sentence.mortalityDiff
        tState.plague.infectiousness += sentence.infectiousnessDiff

        self._info.add(f"Zkusili jste: {sentence.name}. Zafungovalo!")
        if sentence.recoveryDiff != 0:
            self._info.add(f"Šance na uzdravení se změnila o {sentence.recoveryDiff * 100:.2f}%.")
        if sentence.mortalityDiff != 0:
            self._info.add(f"Smrtnost se změnila o {sentence.mortalityDiff * 100:.2f}%.")
        if sentence.infectiousnessDiff != 0:
            self._info.add(f"Nakažlivost se změnila o {sentence.infectiousnessDiff:.2f}%.")

