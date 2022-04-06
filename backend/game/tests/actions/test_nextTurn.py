from game.actions.nextTurn import ActionNextTurn, ActionNextTurnArgs
from game.entities import Entities
from game.state import GameState
from game.tests.actions.common import TEST_ENTITIES, TEST_TEAMS

import pytest

def test_singleTurn():
    state = GameState.createInitial(TEST_TEAMS)
    entities = Entities(TEST_ENTITIES)
    args = ActionNextTurnArgs()

    action = ActionNextTurn(state = state, entities = entities, args = args)

    cost = action.cost()
    assert len(cost) == 0 

    action.commit()
    assert state.turn == 1