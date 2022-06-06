import pytest
from game.actions.common import ActionFailed
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

def test_payResources():
    entities = TEST_ENTITIES
    state = createTestInitState()    
    teamState = state.teamStates[team]
    teamState.resources = {
        entities["res-prace"]: 100,
        entities["res-obyvatel"]: 100,
        entities["res-zamestnanec"]: 100,
        entities["pro-bobule"]: 10,
        entities["pro-drevo"]: 10,
        entities["pro-kuze"]: 1,
    }

    result = teamState.payResources({entities["res-prace"]: 10})
    assert result == {}
    assert teamState.resources == {
        entities["res-prace"]: 90,
        entities["res-obyvatel"]: 100,
        entities["res-zamestnanec"]: 100,
        entities["pro-bobule"]: 10,
        entities["pro-drevo"]: 10,
        entities["pro-kuze"]: 1,
    }

    result = teamState.payResources({entities["res-obyvatel"]: 10})
    assert result == {}
    assert teamState.resources == {
        entities["res-prace"]: 90,
        entities["res-obyvatel"]: 90,
        entities["res-zamestnanec"]: 110,
        entities["pro-bobule"]: 10,
        entities["pro-drevo"]: 10,
        entities["pro-kuze"]: 1,
    }

    result = teamState.payResources({entities["pro-bobule"]: 2, entities["pro-drevo"]: 2})
    assert result == {}
    assert teamState.resources == {
        entities["res-prace"]: 90,
        entities["res-obyvatel"]: 90,
        entities["res-zamestnanec"]: 110,
        entities["pro-bobule"]: 8,
        entities["pro-drevo"]: 8,
        entities["pro-kuze"]: 1,
    }

    result = teamState.payResources({entities["mat-bobule"]: 2, entities["mat-drevo"]: 2, })
    assert result == {entities["mat-bobule"]: 2, entities["mat-drevo"]: 2}
    assert teamState.resources == {
        entities["res-prace"]: 90,
        entities["res-obyvatel"]: 90,
        entities["res-zamestnanec"]: 110,
        entities["pro-bobule"]: 8,
        entities["pro-drevo"]: 8,
        entities["pro-kuze"]: 1,
    }

    result = teamState.payResources({entities["mat-bobule"]: 2, entities["pro-drevo"]: 2, 
                                     entities["res-obyvatel"]:5, entities["res-prace"]:20,})
    assert result == {entities["mat-bobule"]: 2}
    assert teamState.resources == {
        entities["res-prace"]: 70,
        entities["res-obyvatel"]: 85,
        entities["res-zamestnanec"]: 115,
        entities["pro-bobule"]: 8,
        entities["pro-drevo"]: 6,
        entities["pro-kuze"]: 1,
    }

    with pytest.raises(ActionFailed) as einfo:
        teamState.payResources({entities["pro-bobule"]: 10})

    with pytest.raises(ActionFailed) as einfo:
        teamState.payResources({entities["pro-keramika"]: 10})

    with pytest.raises(ActionFailed) as einfo:
        teamState.payResources({entities["res-prace"]: 100})
    

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


def test_homeTiles():
    entities = TEST_ENTITIES
    state = createTestInitState()    
    
    teamState = state.teamStates[entities["tym-zeleni"]]
    tile = teamState.homeTile
    id = tile.entity
    assert id == entities["map-tile05"]


    
