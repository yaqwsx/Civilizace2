from game.actions.actionBase import TeamActionBase
from game.actions.common import ActionException, ActionCost, ActionException
from game.actions.researchStart import ActionResearchArgs

class ActionResearchFinish(TeamActionBase):
    args: ActionResearchArgs


    def cost(self) -> ActionCost:
        return ActionCost()

    def commitInternal(self) -> None:
        if self.args.tech in self.teamState.techs:
            raise ActionException("Technologie <<" + self.args.tech.id + ">> je již vyzkoumána.")

        if not self.args.tech in self.teamState.researching:
            raise ActionException("Výzkum technologie <<" + self.args.tech.id + ">> aktuálně neprobíhá, takže ji nelze dokončit.")

        self.teamState.researching.remove(self.args.tech)
        self.teamState.techs.add(self.args.tech)
        self.info += "Výzkum technologie <<" + self.args.tech.id + ">> byl dokončen."
        # TODO: Přidat samolepky
