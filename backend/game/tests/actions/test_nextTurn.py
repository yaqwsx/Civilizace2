from game.tests.actions.common import createTestInitState
from testing import PYTEST_COLLECT, reimport

if not PYTEST_COLLECT:
    from game.actions.nextTurn import ActionNextTurn, ActionNextTurnArgs
    from game.entities import Entities
    from game.state import GameState
    from game.tests.actions.common import TEST_ENTITIES, TEST_TEAMS


def test_turnCounter():
    reimport(__name__)

    state = createTestInitState()
    entities = TEST_ENTITIES
    state = createTestInitState()
    args = ActionNextTurnArgs()

    action = ActionNextTurn(state = state, entities = entities, args = args)

    cost = action.cost()
    assert len(cost.resources) == 0
    action.commit()
    assert state.turn == 1

    for i in range(20):
        action = ActionNextTurn(state = state, entities = entities, args = args)
        action.commit()
        assert state.turn == i+2
