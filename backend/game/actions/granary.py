from decimal import Decimal
from typing import Dict
from game.actions.actionBase import ActionArgs, ActionBase
from game.entities import Resource, Team, Tech
from game.state import printResourceListForMarkdown

class GranaryArgs(ActionArgs):
    team: Team
    productions: Dict[Resource, int] # int is here on purpose - it does not make sense to use fractions of food

class GranaryAction(ActionBase):

    @property
    def args(self) -> GranaryArgs:
        assert isinstance(self._generalArgs, GranaryArgs)
        return self._generalArgs

    @property
    def description(self):
        return f"Automatizace krmení ({self.args.team.name})"


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

            self.teamState.granary[resource] = self.teamState.granary.get(resource, 0) + amount

        self._info += f"Krmení těmito produkcemi bylo automatizováno: \n{printResourceListForMarkdown(self.args.productions)}"
