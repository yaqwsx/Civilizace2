from typing import Optional, Set
from game.actions.actionBase import TeamActionBase, ActionArgs
from game.actions.common import ActionException, ActionCost
from game.entities import Tech, Team

class ActionResearchArgs(ActionArgs):
    tech: Tech
    task: Optional[str]

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

        if not self.args.task:
            self.info += "**Pozor:** k výzkumu nebyl vybrán úkol."
        else:
            self.info += f"Týmu bude zadán úkol s ID {self.args.task}"

        self.teamState.researching.add(self.args.tech)
        self.info += "Výzkum technologie <<" + self.args.tech.id + ">> začal."
