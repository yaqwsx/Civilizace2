from typing import Dict
from game.actions.common import ActionFailed
from game.actionsNew.actionBaseNew import ActionBaseNew
from game.actionsNew.researchStartNew import ActionResearchArgsNew
from game.entities import Resource, Tech

class ActionResearchFinishNew(ActionBaseNew):

    @property
    def args(self) -> ActionResearchArgsNew:
        assert isinstance(self._generalArgs, ActionResearchArgsNew)
        return self._generalArgs


    def cost(self) -> Dict[Resource, int]:
        return {}

    def _commitImpl(self) -> None:
        if self.args.tech in self.teamState.techs:
            raise ActionFailed(f"Technologie [[{self.args.tech.id}]] je již vyzkoumána.")

        if not self.args.tech in self.teamState.researching:
            raise ActionFailed(f"Výzkum technologie [[{self.args.tech.id}]] aktuálně neprobíhá, takže ji nelze dokončit.")

        self.teamState.researching.remove(self.args.tech)
        self.teamState.techs.add(self.args.tech)
        self._info += "Výzkum technologie [[" + self.args.tech.id + "]] byl dokončen."
