from decimal import Decimal
from typing import Dict
from game.actions.actionBase import ActionArgs
from game.actionsNew.actionBaseNew import ActionBaseNew, ActionFailed
from game.entities import Resource, Team, Tech

class ActionGranaryArgs(ActionArgs):
    team: Team
    productions: Dict[Resource, int] # int is here on purpose - it does not make sense to use fractions of food

class ActionGranary(ActionBaseNew):
    @property
    def args(self) -> ActionGranaryArgs:
        assert isinstance(self._generalArgs, ActionGranaryArgs)
        return self._generalArgs


    def cost(self) -> Dict[Resource, Decimal]:
        return self.args.productions

    def _commitImpl(self) -> None:
        for resource, amount in self.args.productions.items():
            if not resource.isProduction:
                self._errors += "[[" + str(resource) + "]] není produkce"
                continue
            if resource.typ == None or \
                        (resource.typ[0] != self.entities.get("typ-jidlo") and
                         resource.typ[0] != self.entities.get("typ-luxus")):
                self._errors += "[[" + str(resource) + "]] není produkce jídla ani luxusu"
                continue
            if self.teamState.resources[resource] < amount:
                self._errors += "Nelze přesměrovat [[" + str((resource, amount)) + "]], tým vlastní pouze [[" + str((resource, self.teamState.resources[resource]))+ "]]"
                continue

            self.teamState.resources[resource] -= amount
            self.teamState.granary[resource] = self.teamState.granary.get(resource, 0) + amount

        self._info += "Krmení těmito produkcemi bylo automatizováno: [[" + str(self.args.productions) + "]]"
        