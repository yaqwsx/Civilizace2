import os
from django.conf import settings
from game import entityParser
from game.entities import Entities, Tech, Vyroba
from game.state import GameState
from decimal import Decimal
from typing import List

TEST_ENTITIES = entityParser.EntityParser(os.path.join(settings.BASE_DIR, "testEntities.json")).parse()
TEST_TEAM = TEST_ENTITIES["tym-zeleni"]

def createTestInitState(entities=TEST_ENTITIES):
    state = GameState.createInitial(entities)
    state.teamStates[TEST_TEAM].researching.add(entities["tec-c"])
    return state
