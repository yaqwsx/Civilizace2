from decimal import Decimal
from game.actions.actionBase import makeAction
from game.actions.increaseCounter import IncreaseCounterAction, IncreaseCounterArgs
from game.tests.actions.common import TEST_ENTITIES, TEAM_ADVANCED, createTestInitState


teamState = TEAM_ADVANCED
entities = TEST_ENTITIES


def test_something():
    state = createTestInitState()
    entities = TEST_ENTITIES
    args = IncreaseCounterArgs(red=Decimal(5), team=teamState)
    action = makeAction(
        IncreaseCounterAction, state=state, entities=entities, args=args
    )

    req = action.pointsCost()
    action.applyInitiate()
    action.applyCommit(1, 1000)
    assert action.requiresDelayedEffect() == 0
