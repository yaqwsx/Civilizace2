import os
from decimal import Decimal

from django.conf import settings

from game.entities import Entities
from game.entityParser import EntityParser

TEST_ENTITIES = EntityParser.load(
    os.path.join(settings.DATA_PATH, "entities", "TEST.json")
)
TEAM_ADVANCED = TEST_ENTITIES.teams[
    "tym-zeleni"
]  # the developed team for complex testing
TEAM_BASIC = TEST_ENTITIES.teams[
    "tym-cerveni"
]  # the team that is in the initial state, with home tile set up


def createTestInitState(entities: Entities = TEST_ENTITIES):
    from game.state import GameState

    state = GameState.create_initial(entities)
    state.world.combatRandomness = Decimal(0)

    teamEntity = TEAM_ADVANCED
    teamState = state.teamStates[teamEntity]

    # tech
    teamState.researching.add(entities.techs["tec-c"])

    # deploy armies
    # for tileIndex, prestige, equipment in [(0, 10, 1), (3, 15, 5), (30, 20, 15),  (2, 25, 20)]:
    #     tile = state.map.tiles[tileIndex]
    # army = Army(team=team, prestige=prestige, tile=tile.entity, equipment=equipment, assignment=ArmyMode.Occupying)
    # teamState.armies[army.id] = army
    # tile.occupiedBy = army.id

    return state
