from math import ceil, floor
from typing import Dict, List, Optional, Set, Tuple

from pydantic import BaseModel
from game.actions.actionBase import TeamActionBase, ActionArgs
from game.actions.common import ActionException, ActionCost
from game.entities import Entities, Resource, Tech, Team
from game.state import GameState

class FeedRequirements(BaseModel):
    tokensRequired: int
    tokensPerCaste: int
    casteCount: int
    automated: List[Tuple[Resource, int]] # sorted in preferred display order


def computeFeedRequirements(state: GameState, entities: Entities,  team: Team) -> FeedRequirements:
    teamState = state.teamStates[team]
    tokensRequired = ceil(teamState.population / 20)
    foodPerCaste = ceil(tokensRequired / (2*state.casteCount))

    automated = [(production.produces, amount) for production, amount in teamState.granary.items()]
    automatedCount = sum([amount for production, amount in automated if production.typ[0] == entities["typ-jidlo"]])

    automated.sort(key=lambda x: -x[0].typ[1]) # tertiary order: resource level
    automated.sort(key=lambda x: -x[1]) # secondary order: amount
    automated.sort(key=lambda x: 0 if x[0].typ[0] == entities["typ-jidlo"] else 1) # primary order: type

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


    def _addObyvatel(self, amount): # supports negative amounts
        self.teamState.resources[self.entities["res-obyvatel"]] += amount
        if self.teamState.resources[self.entities["res-obyvatel"]] < 0:
            self.teamState.resources[self.entities["res-obyvatel"]] = 0


    def cost(self) -> ActionCost:
        return ActionCost(resources=self.args.materials)


    def commitInternal(self) -> None:
        teamTurn = self.teamState.turn
        worldTurn = self.state.turn

        if teamTurn >= worldTurn:
            raise ActionException(f"Tým už v kole {worldTurn} krmil")

        req = computeFeedRequirements(self.state, self.entities, self.team)

        paidFood = sum(amount for resource, amount in self.args.materials.items() if resource.typ[0] == self.entities["typ-jidlo"])

        newborns = 0
        if req.tokensRequired > paidFood:
            starved = (req.tokensRequired - paidFood) * 5
            self._addObyvatel(-starved)
            self.info += f"Chybí {req.tokensRequired - paidFood} jednotek jídla, takže uhynulo {starved} obyvatel"
            # TODO: Make this a warning, not info
        else:
            newborns += 10

        automated = {x[0]: x[1] for x in req.automated}
        saturated = set()
        for resource, amount in self.args.materials.items():
            if amount + automated.get(resource, 0) >= req.tokensPerCaste:
                saturated.add(resource)
        for resource, amount in automated.items():
            if amount >= req.tokensPerCaste:
                saturated.add(resource)

        food = [x for x in saturated if x.typ[0] == self.entities["typ-jidlo"]]
        food.sort(key=lambda x: -x.typ[1])
        luxus = [x for x in saturated if x.typ[0] == self.entities["typ-luxus"]]
        luxus.sort(key=lambda x: -x.typ[1])

        newborns += sum([x.typ[1] for x in food[:3]])
        newborns += sum([x.typ[1] for x in luxus[:3]]) 

        self._addObyvatel(newborns)

        self.info += f"Krmení úspěšně provedeno. Narodilo se {newborns} nových obyvatel."
        

        self.teamState.resources[self.entities.work] = floor(self.teamState.resources[self.entities.work] / 2)

        reward = {resource.produces: amount for resource, amount in self.teamState.resources.items() if resource.produces != None}
        self.teamState.receiveResources(reward)
        
        self.teamState.turn = worldTurn


        
