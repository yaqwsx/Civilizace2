from typing import Set
from game.actions.actionBase import TeamActionBase, TeamActionArgs
from game.actions.common import ActionArgumentException, ActionCost, ActionFailedException
from game.entities import Tech, TeamEntity

class ActionResearchArgs(TeamActionArgs):
    teamEntity: TeamEntity
    tech: Tech

class ActionResearchStart(TeamActionBase):
    args: ActionResearchArgs

    def _lookupDice(self) -> Set[str]:
        dice = set()
        tech = self.args.tech
        for unlock in tech.unlockedBy:
            if unlock[0] in self.teamState.techs:
                dice.add(unlock[1])
        return dice

    def _checkPrerequisites(self) -> None:
        if self.args.tech in self.teamState.techs:
            raise ActionArgumentException("Technologie <<" + self.args.tech.id + ">> je již vyzkoumána")

        if self.args.tech in self.teamState.researching:
            raise ActionArgumentException("Výzkum technologie <<" + self.args.tech.id + ">> již probíhá")

        dice = self._lookupDice()

        if len(dice) == 0:
            raise ActionArgumentException("Zkoumání technologie <<" + self.args.tech.id + ">> ještě není odemčeno")

    def cost(self) -> ActionCost:
        self._checkPrerequisites()
        return ActionCost(allowedDice = self._lookupDice(), requiredDots = self.args.tech.points, resources = {})

    def apply(self) -> None:
        self._checkPrerequisites()
        self.teamState.researching.add(self.args.tech)
        self.info += "Výzkum technologie <<" + self.args.tech.id + ">> začal."
