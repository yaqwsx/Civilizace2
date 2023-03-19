from decimal import Decimal
from typing import Dict
from game.actions.actionBase import ActionArgs, ActionBase
from game.actions.actionBase import ActionResult
from game.actions.common import ActionFailed
from game.entities import MapTileEntity, Resource, Team

class AddCultureArgs(ActionArgs):
    team: Team
    culture: Decimal

class ActionAddCultureArgs(ActionBase):

    @property
    def args(self) -> AddCultureArgs:
        assert isinstance(self._generalArgs, AddCultureArgs)
        return self._generalArgs


    @property
    def description(self):
        return f"Přidat kulturu týmu {self.args.team.name}"

    def cost(self) -> Dict[Resource, Decimal]:
        return {}

    def _commitImpl(self) -> None:
        if self.args.culture < 0:
            raise ActionFailed("Nemůžu udělit zápornou kulturu")
        tState = self.teamState
        assert tState is not None
        c = self.entities["res-kultura"]
        tState.resources[c] = tState.resources.get(c, 0) + self.args.culture
        self._info.add(f"Tým dostal {self.args.culture} kultury. Nyní má {tState.resources[c]}.")
