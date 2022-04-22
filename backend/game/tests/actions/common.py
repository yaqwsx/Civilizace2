import os
from django.conf import settings
from game import entityParser
from game.entities import Entities, Team, Tech, Vyroba, Resource
from game.state import Army, ArmyId, ArmyState, GameState
from game.actions.assignStartTile import ActionAssignTile, ActionAssignTileArgs
from decimal import Decimal
from typing import Dict, List

TEST_ENTITIES = entityParser.loadEntities(os.path.join(settings.BASE_DIR, "testEntities.json"))
TEAM_ADVANCED = TEST_ENTITIES["tym-zeleni"] # the developed team for complex testing
TEAM_BASIC = TEST_ENTITIES["tym-cerveni"] # the team that is in the initial state, with home tile set up


def createTestInitState(entities=TEST_ENTITIES):
    state = GameState.createInitial(entities)    
    
    #starting tiles
    for index, team in enumerate(entities.teams.values()):
        ActionAssignTile(args=ActionAssignTileArgs(team=team, index=4*index + 1), state=state, entities=entities).commit()
    
    team = TEAM_ADVANCED
    teamState = state.teamStates[TEAM_ADVANCED]

    # tech
    teamState.researching.add(entities["tec-c"])

    # roads
    home = state.map.getHomeTile(TEAM_ADVANCED)
    home.roadsTo = [state.map.tiles[x].entity for x in [6, 10, 24, 2]]

    # deploy armies
    for tileIndex, prestige, equipment in [(0, 10, 1), (3, 15, 5), (30, 20, 15),  (2, 25, 20)]:
        tile = state.map.tiles[tileIndex]
        army = Army(team=team, prestige=prestige, tile=tile.entity, equipment=equipment, state=ArmyState.Occupying)
        teamState.armies[army.id] = army
        tile.occupiedBy = army.id

    return state
        