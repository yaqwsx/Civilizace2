from game.actions.actionBase import NoInitActionBase
from game.tests.actions.common import createTestInitState
from testing import PYTEST_COLLECT, reimport

if not PYTEST_COLLECT:
    from game.actions.nextTurn import NextTurnAction, NextTurnArgs
    from game.tests.actions.common import TEST_ENTITIES


def test_turnCounter():
    reimport(__name__)

    entities = TEST_ENTITIES
    state = createTestInitState()
    args = NextTurnArgs()

    action = NextTurnAction.makeAction(state=state, entities=entities, args=args)

    assert isinstance(NextTurnAction, NoInitActionBase)
    action.commit()
    assert state.world.turn == 1

    for i in range(20):
        action = NextTurnAction.makeAction(state=state, entities=entities, args=args)
        action.applyCommit()
        assert state.world.turn == i + 2


def test_richnessIncrease():
    reimport(__name__)
    entities = TEST_ENTITIES
    state = createTestInitState()
    args = NextTurnArgs()

    action = NextTurnAction.makeAction(state=state, entities=entities, args=args)
    for tile in state.map.tiles.values():
        assert tile.richnessTokens == tile.richness
        tile.richnessTokens = 0

    for i in range(10):
        action.commit()

    for tile in state.map.tiles.values():
        assert tile.richnessTokens == tile.entity.richness
