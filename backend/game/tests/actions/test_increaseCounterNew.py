from decimal import Decimal

from game.actions.increaseCounter import IncreaseCounterAction, IncreaseCounterArgs
from game.tests.actions.common import TEAM_ADVANCED, TEST_ENTITIES, createTestInitState

teamState = TEAM_ADVANCED
entities = TEST_ENTITIES


def test_something():
    state = createTestInitState()
    entities = TEST_ENTITIES
    args = IncreaseCounterArgs(red=Decimal(5), team=teamState)
    action = IncreaseCounterAction.makeAction(state=state, entities=entities, args=args)

    req = action.pointsCost()
    action.applyInitiate()
    commitResult = action.commitThrows(throws=1, dots=1000)
    assert len(commitResult.scheduledActions) == 0
