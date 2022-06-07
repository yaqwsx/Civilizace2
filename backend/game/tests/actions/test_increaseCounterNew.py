from decimal import Decimal
from game.actions.increaseCounter import ActionIncreaseCounter, ActionIncreaseCounterArgs
from game.tests.actions.common import TEST_ENTITIES, TEAM_ADVANCED, createTestInitState
from game.state import GameState
from game.actions.common import ActionException

import pytest

team = TEAM_ADVANCED
entities = TEST_ENTITIES

def test_something():
    state = createTestInitState()
    entities = TEST_ENTITIES
    args = ActionIncreaseCounterArgs(red=Decimal(5), team=team)
    action = ActionIncreaseCounter(state=state, entities=entities, args=args)

    req = action.diceRequirements()
    action.applyInitiate()
    action.applyCommit(1, 1000)
    assert action.requiresDelayedEffect() == 0
