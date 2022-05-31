from decimal import Decimal

from game.actions.actionBase import TeamActionBase, ActionArgs
from game.entities import Resource
from game.actions.common import ActionCost, ActionException, MessageBuilder, ActionException
from typing import Optional

# This action is a demonstration of action implementation. Basically you can say
# how much to increase the red Counter. Optionally we can pass an entity (e.g.,
# the player sacrificed to gods) and then it gains some blue counter

class ActionIncreaseCounterArgs(ActionArgs):
    red: Decimal
    resource: Optional[Resource]=None

class ActionIncreaseCounter(TeamActionBase):
    args: ActionIncreaseCounterArgs

    def cost(self) -> ActionCost:
        return ActionCost(resources={
            self.entities["res-prace"]: Decimal(10),
            self.entities["mat-drevo"]: Decimal(5)
        })

    def commitInternal(self) -> None:
        error = MessageBuilder()

        if self.args.red > 10:
            error += "Hráč nemůže zvýšit červené počitado o více než 10"
        if self.args.red < -10:
            error += "Hráč nemůže snížit počitadlo o více než 10"
        if self.args.resource is not None and self.args.resource.id == "mat-clovek":
            error += "Hráči nemohou obětovat lidi - chtěli jste obětovat 1× [[mat-clovek]]"

        if not error.empty:
            raise ActionException(error)

        self.teamState.redCounter += self.args.red
        if self.args.resource is not None:
            self.teamState.blueCounter += 1
