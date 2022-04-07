from decimal import Decimal
from game.state import GameState, TeamId
from game.entities import Resource, Entities
from game.actions.common import ActionCost, TeamActionArgs, ActionFailedException, MessageBuilder
from typing import Optional

# This action is a demonstration of action implementation. Basically you can say
# how much to increase the red Counter. Optionally we can pass an entity (e.g.,
# the player sacrificed to gods) and then it gains some blue counter

class IncreaseCounterArgs(TeamActionArgs):
    red: Decimal
    resource: Optional[Resource]

def increaseCounterCost(teamId: TeamId, entities: Entities, state: GameState) \
        -> ActionCost:
    return {
        "res-prace": Decimal(10),
        "mat-drevo": Decimal(5)
    }

def commitCounterCost(args: IncreaseCounterArgs,
                      entities: Entities,
                      state: GameState) \
        -> None:
    error = MessageBuilder()

    if args.red > 10:
        error += "Hráč nemůže zvýšit červené počitado o více než 10"
    if args.red < -10:
        error += "Hráč nemůže snížit počitadlo o více než 10"
    if args.resource is not None and args.resource.id == "mat-clovek":
        error += "Hráči nemohou obětovat lidi - chtěli jste obětovat 1× <<mat-clovek>>"

    if not error.empty:
        raise ActionFailedException(error)

    state.teamStates[args.teamId].redCounter += args.red
    if args.resource is not None:
        state.teamStates[args.teamId].blueCounter += 1
