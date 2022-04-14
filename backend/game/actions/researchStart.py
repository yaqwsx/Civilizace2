from typing import List
from pydantic import BaseModel
from game.actions.actionBase import ActionBase, TeamActionBase
from game.actions.common import ActionArgumentException, ActionCost, ActionFailedException
from game.entities import Tech
from game.state import TeamId, TeamState

class ActionResearchArgs(BaseModel):
    tech: Tech

class ActionResearchStart(TeamActionBase):
    args: ActionResearchArgs

    def _lookupDice(self) -> List[str]:
        dice = []
        for tech in self.teamState.techs:
            print(tech.id)
            if self.args.tech in tech.edges.keys():
                print("  OK")
                dice.append(tech.edges[self.args.tech])
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
        return ActionCost(allowedDice = self._lookupDice(), requiredDots = self.args.tech.diePoints, resources = {})

    def apply(self) -> None:
        self._checkPrerequisites()
        self.teamState.researching.add(self.args.tech)
        self.info += "Výzkum technologie <<" + self.args.tech.id + ">> začal."
