from decimal import Decimal

from game.actions.actionBase import TeamActionBase, TeamActionArgs
from game.state import GameState, TeamId
from game.entities import Resource, Entities, Team
from game.actions.common import ActionCost, ActionFailedException, MessageBuilder, ActionArgumentException
from typing import Optional

# This action is a demonstration of action implementation. Basically you can say
# how much to increase the red Counter. Optionally we can pass an entity (e.g.,
# the player sacrificed to gods) and then it gains some blue counter

class ActionAssignTileArgs(TeamActionArgs):
    tileId: int

class ActionIncreaseCounter(TeamActionBase):
    args: ActionAssignTileArgs

    def cost(self) -> ActionCost:
        return ActionCost()

    def commit(self) -> None:
        None
