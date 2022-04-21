from decimal import Decimal
from game.actions.increaseCounter import ActionIncreaseCounter, ActionIncreaseCounterArgs
from game.tests.actions.common import TEST_ENTITIES, TEAM_ADVANCED, createTestInitState
from game.state import GameState
from game.actions.common import ActionException

import pytest

team = TEAM_ADVANCED
entities = TEST_ENTITIES

def test_withoutResources():
    state = createTestInitState()
    entities = TEST_ENTITIES
    args = ActionIncreaseCounterArgs(red=Decimal(5), team=team)
    action = ActionIncreaseCounter(state=state, entities=entities, args=args)

    cost = action.cost()

    assert cost.resources[entities["res-prace"]] == 10
    assert cost.resources[entities["mat-drevo"]] == 5
    assert len(cost.resources) == 2

    prev = state.teamStates[team].blueCounter
    action.commit()
    t = state.teamStates[team]
    assert t.redCounter == 5
    assert t.blueCounter == prev


def test_withResources():
    state = createTestInitState()
    args = ActionIncreaseCounterArgs(red=Decimal(5), resource=TEST_ENTITIES["mat-drevo"], team=team)
    action = ActionIncreaseCounter(state=state, entities=entities, args=args)

    prev = state.teamStates[team].blueCounter
    action.commit()
    t = state.teamStates[team]
    assert t.redCounter == 5
    assert t.blueCounter != prev
    assert t.blueCounter == 1


def test_tooMany():
    state = GameState.createInitial(TEST_ENTITIES)
    args = ActionIncreaseCounterArgs(red=Decimal(12), team=team)
    action = ActionIncreaseCounter(state=state, entities=entities, args=args)

    with pytest.raises(ActionException) as einfo:
        action.commit()
    assert "zvýšit" in str(einfo.value)

