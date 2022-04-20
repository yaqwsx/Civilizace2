from typing import Set
from game.actions.actionBase import TeamActionBase, TeamActionArgs
from game.actions.common import ActionException, ActionCost
from game.entities import Tech, Team

class ActionResearchArgs(TeamActionArgs):
    team: Team
    tech: Tech

class ActionResearchStart(TeamActionBase):
    args: ActionResearchArgs


    def cost(self) -> ActionCost:
        dice = self.teamState.getUnlockingDice(self.args.tech)
        if len(dice) == 0:
            raise ActionException("Zkoumání technologie <<" + self.args.tech.id + ">> ještě není odemčeno")
        return ActionCost(allowedDice=dice, requiredDots=self.args.tech.points, resources=self.args.tech.cost)


    def commitInternal(self) -> None:
        if self.args.tech in self.teamState.techs:
            raise ActionException("Technologie <<" + self.args.tech.id + ">> je již vyzkoumána")

        if self.args.tech in self.teamState.researching:
            raise ActionException("Výzkum technologie <<" + self.args.tech.id + ">> již probíhá")

        self.teamState.researching.add(self.args.tech)
        self.info += "Výzkum technologie <<" + self.args.tech.id + ">> začal."
