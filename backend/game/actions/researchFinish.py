from math import ceil
from typing import Dict
from game.actions.actionBase import ActionBase, ActionFailed
from game.actions.researchStart import ResearchArgs
from game.entities import Resource


class ResearchFinishArgs(ResearchArgs):
    pass


class ResearchFinishAction(ActionBase):
    @property
    def args(self) -> ResearchFinishArgs:
        assert isinstance(self._generalArgs, ResearchFinishArgs)
        return self._generalArgs

    @property
    def description(self):
        return f"Dokončení výzkumu {self.args.tech.name} ({self.args.team.name})"

    def cost(self) -> Dict[Resource, int]:
        return {}

    def _commitImpl(self) -> None:
        if self.args.tech in self.teamState.techs:
            raise ActionFailed(
                f"Technologie [[{self.args.tech.id}]] je již vyzkoumána.")

        if not self.args.tech in self.teamState.researching:
            raise ActionFailed(
                f"Výzkum technologie [[{self.args.tech.id}]] aktuálně neprobíhá, takže ji nelze dokončit.")

        self.teamState.researching.remove(self.args.tech)
        self.teamState.techs.add(self.args.tech)
        self._info += "Výzkum technologie [[" + \
            self.args.tech.id + "]] byl dokončen."
        self._info += f"Vydejte týmu puntík na kostku"
        dice = ", ".join(
            [die.name for die in self.teamState.getUnlockingDice(self.args.tech)])
        self._info += f"Vydejte týmu jeden žeton objevu: {dice}"
