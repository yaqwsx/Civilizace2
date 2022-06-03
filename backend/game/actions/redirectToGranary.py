from typing import Dict
from game.actions.actionBase import ActionArgs, TeamActionBase
from game.actions.common import ActionException, ActionCost, ActionException
from game.actions.researchStart import ActionResearchArgs
from game.entities import Resource, Team, Tech

class ActionRedirectArgs(ActionArgs):
    team: Team
    productions: Dict[Resource, int] # int is here on purpose - it does not make sense to use fractions of food

class ActionRedirect(TeamActionBase):
    args: ActionRedirectArgs

    def cost(self) -> ActionCost:
        return ActionCost(resources=self.args.productions)

    def commitInternal(self) -> None:
        for resource, amount in self.args.productions.items():
            if not resource.isProduction:
                raise ActionException("[[" + str(resource) + "]] není produkce")
            if resource.typ == None or \
                        (resource.typ[0] != self.entities.get("typ-jidlo") and
                         resource.typ != self.entities.get("typ-luxus")):
                raise ActionException("[[" + str(resource) + "]] není produkce jídla ani luxusu")
            if self.teamState.resources[resource] < amount:
                raise ActionException("Nelze přesměrovat [[" + str((resource, amount)) + "]], tým vlastní pouze [[" + str((resource, self.teamState.resources[resource]))+ "]]")

            self.teamState.resources[resource] -= amount
            self.teamState.granary[resource] = self.teamState.granary.get(resource, 0) + amount

        self.info += "Krmení těmito produkcemi bylo automatizováno: [[" + str(self.args.productions) + "]]"
        