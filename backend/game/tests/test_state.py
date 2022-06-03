from game.state import GameState
from game.gameGlue import stateSerialize, stateDeserialize
from game.tests.actions.common import TEAM_BASIC, TEST_ENTITIES, createTestInitState
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
    assert x.map._parent == x.teamStates[TEST_ENTITIES["tym-zeleni"]]._parent
    assert y.map._parent == y.teamStates[TEST_ENTITIES["tym-zeleni"]]._parent

    sRepr = json.dumps(s)
    jRepr = json.loads(sRepr)
    z = stateDeserialize(GameState, jRepr, TEST_ENTITIES)
    assert x == z
    assert z.map._parent == z.teamStates[TEST_ENTITIES["tym-zeleni"]]._parent


team = TEAM_BASIC

def test_receiveResources():
    entities = TEST_ENTITIES
    state = createTestInitState()    
    teamState = state.teamStates[team]

    teamState.storage = {}
    teamState.resources = {}
    
    withdraw = teamState.receiveResources({})
    assert teamState.resources == {}
    assert teamState.storage == {}
    assert withdraw == {}

    withdraw = teamState.receiveResources({entities["mat-kuze"]:2}, instantWithdraw=True)
    assert teamState.resources == {}
    assert teamState.storage == {}
    assert withdraw == {entities["mat-kuze"]:2}

    withdraw = teamState.receiveResources({entities["mat-kuze"]:2})
    assert teamState.resources == {}
    assert teamState.storage == {entities["mat-kuze"]:2}
    assert withdraw == {}

    withdraw = teamState.receiveResources({entities["pro-kuze"]:3})
    assert teamState.resources == {entities["pro-kuze"]:3}
    assert teamState.storage == {entities["mat-kuze"]:2}
    assert withdraw == {}

    withdraw = teamState.receiveResources({entities["pro-kuze"]:10, entities["mat-kuze"]: 10})
    assert teamState.resources == {entities["pro-kuze"]:13}
    assert teamState.storage == {entities["mat-kuze"]:10}
    assert withdraw == {}




    
