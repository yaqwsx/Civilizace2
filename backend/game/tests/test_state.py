from game.state import GameState
from game.tests.actions.common import TEST_ENTITIES, createTestInitState

def test_stateEq():
    x = createTestInitState()
    y = createTestInitState()
    assert x == y

    y.turn = 42
    assert x != y

def test_serialize():
    x = createTestInitState()
    s = x.serialize()
    y = GameState.deserialize(s, TEST_ENTITIES)
    assert x == y
