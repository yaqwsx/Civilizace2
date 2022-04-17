from decimal import Decimal
from game.actions.increaseCounter import ActionIncreaseCounter, ActionIncreaseCounterArgs
from game.tests.actions.common import TEST_ENTITIES, TEST_TEAM, createTestInitState
from game.state import GameState
from game.actions.common import ActionFailedException

import pytest

team = TEST_TEAM
entities = TEST_ENTITIES

def test_withoutResources():
    state = createTestInitState()
    args = ActionIncreaseCounterArgs(red=Decimal(5), teamEntity=team)
    action = ActionIncreaseCounter(state=state, entities=entities, args=args)

    cost = action.cost()

    assert cost["res-prace"] == 10
    assert cost["mat-drevo"] == 5
    assert len(cost) == 2

    prev = state.teamStates[team].blueCounter
    action.commit()
    t = state.teamStates[team]
    assert t.redCounter == 5
    assert t.blueCounter == prev


def test_withResources():
    state = createTestInitState()
    args = ActionIncreaseCounterArgs(red=Decimal(5), resource=TEST_ENTITIES["mat-drevo"], teamEntity=team)
    action = ActionIncreaseCounter(state=state, entities=entities, args=args)

    prev = state.teamStates[team].blueCounter
    action.commit()
    t = state.teamStates[team]
    assert t.redCounter == 5
    assert t.blueCounter != prev
    assert t.blueCounter == 1


def test_tooMany():
    state = GameState.createInitial(TEST_ENTITIES)
    args = ActionIncreaseCounterArgs(red=Decimal(12), teamEntity=team)
    action = ActionIncreaseCounter(state=state, entities=entities, args=args)

    with pytest.raises(ActionFailedException) as einfo:
        action.commit()
    assert "zvýšit" in str(einfo.value)

