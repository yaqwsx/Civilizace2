from math import ceil
from typing import Dict, Optional, Set

from pydantic import BaseModel
from game.actions.actionBase import TeamActionBase, ActionArgs
from game.actions.common import ActionException, ActionCost
from game.entities import Entities, Resource, Tech, Team
from game.state import GameState

class FeedRequirements(BaseModel):
    tokensRequired: int
    tokensPerCaste: int
    casteCount: int
    automated: Dict[Resource, int]


def computeFeedRequirements(state: GameState, entities: Entities,  team: Team) -> FeedRequirements:
    teamState = state.teamStates[team]
    tokensRequired = ceil(teamState.population / 20)
    foodPerCaste = ceil(teamState.population / state.casteCount)

    automated = {production.produces: amount for production, amount in teamState.granary.items()}
    automatedCount = sum([amount for production, amount in automated if production.typ == entities["typ-jidlo"]])

    return FeedRequirements(
        tokensRequired=tokensRequired-automatedCount,
        tokensPerCaste=foodPerCaste,
        casteCount=state.casteCount,
        automated=automated
    )


class ActionFeedArgs(ActionArgs):
    team: Team
    materials: Dict[Resource, int]

class ActionFeed(TeamActionBase):
    args: ActionFeedArgs


    def cost(self) -> ActionCost:
        return ActionCost(resources=self.args.materials)


    def commitInternal(self) -> None:
        teamTurn = self.teamState.turn
        worldTurn = self.state.turn

        if teamTurn >= worldTurn:
            raise ActionException(f"Tým už v kole {worldTurn} krmil")

        foodPerCaste = ceil(self.teamState.population / self.state.casteCount)

        granaryFood = {production.produces: amount for production, amount in self.teamState.granary.items() if production.typ == self.entities["typ-jidlo"]}
        granaryLuxury = {production.produces: amount for production, amount in self.teamState.granary.items() if production.typ == self.entities["typ-luxus"]}

        
