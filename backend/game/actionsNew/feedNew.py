from decimal import Decimal
from math import ceil, floor
from typing import Dict, List, Tuple

from pydantic import BaseModel
from game.actions.actionBase import ActionArgs
from game.actionsNew.actionBaseNew import ActionBaseNew, ActionFailed
from game.entities import Entities, Resource, Team
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

class ActionFeed(ActionBaseNew):

    @property
    def args(self) -> ActionFeedArgs:
        assert isinstance(self._generalArgs, ActionFeedArgs)
        return self._generalArgs


    def _addObyvatel(self, amount): # supports negative amounts
        self.teamState.resources[self.entities["res-obyvatel"]] += amount
        if self.teamState.resources[self.entities["res-obyvatel"]] < 0:
            self.teamState.resources[self.entities["res-obyvatel"]] = 0


    def cost(self) -> Dict[Resource, Decimal]:
        return self.args.materials


    def _commitImpl(self) -> None:
        teamTurn = self.teamState.turn
        worldTurn = self.state.turn

        if teamTurn >= worldTurn:
            raise ActionFailed(f"Tým už v kole {worldTurn} krmil")

        req = computeFeedRequirements(self.state, self.entities, self.args.team)

        paidFood = sum(amount for resource, amount in self.args.materials.items() if resource.typ[0] == self.entities["typ-jidlo"])

        newborns = 0
        if req.tokensRequired > paidFood:
            starved = (req.tokensRequired - paidFood) * 5
            self._addObyvatel(-starved)
            self._warnings += f"Chybí {req.tokensRequired - paidFood} jednotek jídla, takže uhynulo {starved} obyvatel"
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

        self._info += f"Krmení úspěšně provedeno. Narodilo se {newborns} nových obyvatel."
        

        self.teamState.resources[self.entities.work] = floor(self.teamState.resources[self.entities.work] / 2)

        reward = {resource.produces: amount for resource, amount in self.teamState.resources.items() if resource.produces != None}
        self.teamState.receiveResources(reward)
        
        self.teamState.turn = worldTurn


        