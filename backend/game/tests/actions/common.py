import os
from django.conf import settings
from game import entityParser

TEST_ENTITIES = entityParser.loadEntities(os.path.join(settings.DATA_PATH, "entities", "TEST.json"))
TEAM_ADVANCED = TEST_ENTITIES["tym-zeleni"] # the developed team for complex testing
TEAM_BASIC = TEST_ENTITIES["tym-cerveni"] # the team that is in the initial state, with home tile set up


def createTestInitState(entities=TEST_ENTITIES):
    from game.state import Army, ArmyState, GameState

    state = GameState.createInitial(entities)

    team = TEAM_ADVANCED
    teamState = state.teamStates[TEAM_ADVANCED]

    # tech
    teamState.researching.add(entities["tec-c"])

    # roads
    state.teamStates[entities["tym-modri"]].roadsTo = set([state.map.tiles[x].entity for x in [6, 10, 24, 2]])

    # deploy armies
    for tileIndex, prestige, equipment in [(0, 10, 1), (3, 15, 5), (30, 20, 15),  (2, 25, 20)]:
        tile = state.map.tiles[tileIndex]
        army = Army(team=team, prestige=prestige, tile=tile.entity, equipment=equipment, state=ArmyState.Occupying)
        teamState.armies[army.id] = army
        tile.occupiedBy = army.id

    return state
