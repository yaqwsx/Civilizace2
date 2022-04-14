from typing import List
from pydantic import BaseModel
from game.actions.actionBase import ActionBase, TeamActionBase
from game.actions.common import ActionArgumentException, ActionCost, ActionFailedException
from game.actions.researchStart import ActionResearchArgs
from game.entities import Tech
from game.state import TeamId, TeamState

class ActionResearchFinish(TeamActionBase):
    args: ActionResearchArgs

    def _checkPrerequisites(self) -> None:
        if self.args.tech in self.teamState.techs:
            raise ActionArgumentException("Technologie <<" + self.args.tech.id + ">> je již vyzkoumána.")

        if not self.args.tech in self.teamState.researching:
            raise ActionArgumentException("Výzkum technologie <<" + self.args.tech.id + ">> aktuálně neprobíhá, takže ji nelze dokončit.")

    def cost(self) -> ActionCost:
        self._checkPrerequisites()
        return ActionCost()

    def apply(self) -> None:
        self._checkPrerequisites()
        self.teamState.researching.remove(self.args.tech)
        self.teamState.techs.add(self.args.tech)
        self.info += "Výzkum technologie <<" + self.args.tech.id + ">> byl dokončen."
        # TODO: Přidat samolepky
