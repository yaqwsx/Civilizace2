import os
from django.conf import settings
from game import entityParser
from game.entities import Entities, Tech, Vyroba, Resource
from game.state import GameState
from game.actions.assignStartTile import ActionAssignTile, ActionAssignTileArgs
from decimal import Decimal
from typing import Dict, List

TEST_ENTITIES = entityParser.EntityParser(os.path.join(settings.BASE_DIR, "testEntities.json")).parse()
TEAM_ADVANCED = TEST_ENTITIES["tym-zeleni"] # the developed team for complex testing
TEAM_BASIC = TEST_ENTITIES["tym-cerveni"] # the team that is in the initial state, with the pre-game set up
TEAM_INIT = TEST_ENTITIES["tym-cerni"] # team that is in the initial state, before pre-game


def createTestInitState(entities=TEST_ENTITIES):
    state = GameState.createInitial(entities)
    state.teamStates[TEAM_ADVANCED].researching.add(entities["tec-c"])
    for index, team in enumerate(entities.teams.values()):
        if team == TEAM_INIT:
            continue
        ActionAssignTile(args=ActionAssignTileArgs(team=team, index=4*index + 1), state=state, entities=entities).commit()
    return state
        