import os
from django.conf import settings
from game import entityParser
from game.entities import Entities, Tech, Vyroba
from game.state import GameState
from game.actions.assignStartTile import ActionAssignTile, ActionAssignTileArgs
from decimal import Decimal
from typing import List

TEST_ENTITIES = entityParser.EntityParser(os.path.join(settings.BASE_DIR, "testEntities.json")).parse()
TEST_TEAM = TEST_ENTITIES["tym-zeleni"]

def createTestInitState(entities=TEST_ENTITIES):
    state = GameState.createInitial(entities)
    state.teamStates[TEST_TEAM].researching.add(entities["tec-c"])
    return state

def createTestInitStateWithHomeTiles(entities=TEST_ENTITIES):
    state = createTestInitState(entities)
    for index, team in enumerate(entities.teams.values()):
        ActionAssignTile(args=ActionAssignTileArgs(team=team, index=4*index + 1), state=state, entities=entities).commit()
    return state
