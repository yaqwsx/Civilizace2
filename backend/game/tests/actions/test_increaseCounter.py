from game.tests.actions.common import TEST_TEAMS, TEST_ENTITIES
from game.state import GameState
from game.actions.common import ActionException
from game.actions.increaseCounter import increaseCounterCost, IncreaseCounterArgs, commitCounterCost

import pytest

def test_withoutResources():
    state = GameState.createInitial(TEST_TEAMS, TEST_ENTITIES)
    cost = increaseCounterCost("tym-zeleny", TEST_ENTITIES, state)
    assert cost["res-prace"] == 10
    assert cost["mat-drevo"] == 5
    assert len(cost) == 2

    arg = IncreaseCounterArgs(
        teamId="tym-zeleny",
        red=5,
        resource=None
    )

    prev = state.teamStates["tym-zeleny"].blueCounter
    commitCounterCost(arg, TEST_ENTITIES, state)
    t = state.teamStates["tym-zeleny"]
    assert t.redCounter == 5
    assert t.blueCounter == prev

def test_withResources():
    state = GameState.createInitial(TEST_TEAMS, TEST_ENTITIES)
    arg = IncreaseCounterArgs(
        teamId="tym-zeleny",
        red=5,
        resource=TEST_ENTITIES["mat-drevo"]
    )

    prev = state.teamStates["tym-zeleny"].blueCounter
    commitCounterCost(arg, TEST_ENTITIES, state)
    t = state.teamStates["tym-zeleny"]
    assert t.redCounter == 5
    assert t.blueCounter != prev
    assert t.blueCounter == 1

def test_tooMany():
    state = GameState.createInitial(TEST_TEAMS, TEST_ENTITIES)

    arg = IncreaseCounterArgs(
        teamId="tym-zeleny",
        red=12,
        resource=None
    )
    with pytest.raises(ActionException) as einfo:
        commitCounterCost(arg, TEST_ENTITIES, state)
    assert "zvýšit" in str(einfo.value)

