from decimal import Decimal
from math import ceil
import random
from typing import Dict
from pydantic import BaseModel
from game.actions.actionBase import ActionArgs
from game.actions.actionBase import ActionBase
from game.entities import Resource

class ActionPlagueTickArgs(ActionArgs):
    pass

class ActionPlagueTick(ActionBase):
    @property
    def args(self) -> ActionPlagueTickArgs:
        assert isinstance(self._generalArgs, ActionPlagueTickArgs)
        return self._generalArgs

    def cost(self) -> Dict[Resource, Decimal]:
        return {}


    def _commitImpl(self) -> None:

        for team in self.state.teamStates.values():
            plague = team.plague

            # sireni
            for i in range(ceil(plague.sick / 10)):
                # pick 10 random people
                # infect them
                None
            
            # vyhodnoceni
            for i in range(plague.sick):
                result = random(100)

                if result < plague.mortality:
                    #die
                    None
                if result > 100-plague.recovery:
                    #heal
                    None


        self._info += "Mor se rozšířil"
