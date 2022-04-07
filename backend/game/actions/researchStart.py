from pydantic import BaseModel
from game.actions.actionBase import ActionBase
from game.actions.common import ActionCost, ActionException
from game.entities import Tech
from game.state import TeamId, TeamState

class ActionResearchStartArgs(BaseModel):
    tech: Tech
    team: TeamId

class ActionResearchStart(ActionBase):
    args: ActionResearchStartArgs

    def team(self) -> TeamState:
        return self.state.teamStates[self.args.team]

    def cost(self) -> ActionCost:
        if self.args.tech in self.team().techs:
            raise ActionException("Technologie <<" + self.args.tech.id + ">> je již vyzkoumána")

        if self.args.tech in self.team().researching:
            raise ActionException("Výzkum technologie <<" + self.args.tech.id + ">> již probíhá")

        dice = []
        for tech in self.team().techs:
            if self.args.tech in tech.edges.keys():
                dice.append(tech.edges[self.args.tech])

        if len(dice) == 0:
            raise ActionException("Zkoumání technologie <<" + self.args.tech.id + ">> ještě není odemčeno")

        return ActionCost(allowedDice = dice, requiredDots = self.args.tech.diePoints, resources = {})

    def apply(self) -> None:
        if self.args.tech in self.team().techs:
            return "Zkoumání technologie <<" + self.args.tech.id + " již bylo dokončeno."
        
        self.team().researching.append(self.args.tech)
        self.info += "Výzkum technologie <<" + self.args.tech.id + ">> začal."
