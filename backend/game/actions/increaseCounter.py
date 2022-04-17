from decimal import Decimal

from pydantic import BaseModel
from game.actions.actionBase import TeamActionBase, TeamActionArgs
from game.state import GameState, TeamId
from game.entities import Resource, Entities, Team
from game.actions.common import ActionCost, ActionFailedException, MessageBuilder, ActionArgumentException
from typing import Optional

# This action is a demonstration of action implementation. Basically you can say
# how much to increase the red Counter. Optionally we can pass an entity (e.g.,
# the player sacrificed to gods) and then it gains some blue counter

class ActionIncreaseCounterArgs(TeamActionArgs):
    red: Decimal
    resource: Optional[Resource]=None

class ActionIncreaseCounter(TeamActionBase):
    args: ActionIncreaseCounterArgs

    def cost(self) -> ActionCost:
        return {
            "res-prace": Decimal(10),
            "mat-drevo": Decimal(5)
        }

    def commit(self) -> None:
        error = MessageBuilder()

        if self.args.red > 10:
            error += "Hráč nemůže zvýšit červené počitado o více než 10"
        if self.args.red < -10:
            error += "Hráč nemůže snížit počitadlo o více než 10"
        if self.args.resource is not None and self.args.resource.id == "mat-clovek":
            error += "Hráči nemohou obětovat lidi - chtěli jste obětovat 1× <<mat-clovek>>"

        if not error.empty:
            raise ActionFailedException(error)

        self.teamState.redCounter += self.args.red
        if self.args.resource is not None:
            self.teamState.blueCounter += 1
