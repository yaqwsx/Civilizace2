from game.state import GameState
from game.gameGlue import stateSerialize, stateDeserialize
from game.tests.actions.common import TEST_ENTITIES, createTestInitState
import json

def test_stateEq():
    x = createTestInitState()
    y = createTestInitState()
    assert x == y

    y.turn = 42
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
