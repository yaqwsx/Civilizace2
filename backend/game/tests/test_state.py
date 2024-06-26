import json

from core.management.commands.addarmies import addArmies
from game.gameGlue import stateDeserialize, stateSerialize
from game.state import GameState
from game.tests.actions.common import TEST_ENTITIES, createTestInitState


def test_stateEq():
    x = createTestInitState()
    y = createTestInitState()
    assert x == y

    y.world.turn = 42
    assert x != y


def test_serialize():
    x = createTestInitState()
    s = stateSerialize(x)
    y = stateDeserialize(GameState, s, TEST_ENTITIES)
    assert x == y

    sRepr = json.dumps(s)
    jRepr = json.loads(sRepr)
    z = stateDeserialize(GameState, jRepr, TEST_ENTITIES)
    assert x == z


def test_homeTiles():
    entities = TEST_ENTITIES
    state = createTestInitState()

    teamState = state.teamStates[entities.teams["tym-zeleni"]]
    tile_entity = teamState.team.homeTile
    assert tile_entity.id == "map-tile05"
    assert tile_entity == entities.tiles["map-tile05"]


def test_addArmies():
    entities = TEST_ENTITIES
    state = createTestInitState()

    addArmies(state)
    assert len(state.map.armies) == 32
    assert state.map.armies[30].team.id == "tym-fialovi"
    assert state.map.armies[30].name == "D"

    addArmies(state)
    assert len(state.map.armies) == 40
    assert state.map.armies[36].team.id == "tym-modri"
    assert state.map.armies[36].name == "E"
