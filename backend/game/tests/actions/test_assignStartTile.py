from backend.game.actions.common import ActionCost
from game.actions.assignStartTile import ActionAssignTile, ActionAssignTileArgs
from game.tests.actions.common import createTestInitState
from testing import PYTEST_COLLECT, reimport

if not PYTEST_COLLECT:
    from game.actions.nextTurn import ActionNextTurn, ActionNextTurnArgs
    from game.entities import Entities
    from game.state import GameState
    from game.tests.actions.common import TEST_ENTITIES, TEST_TEAM


def test_initialState():
    reimport(__name__)

    state = createTestInitState()
    entities = TEST_ENTITIES
    assert len(state.map.tiles) == 24, "Empty map should have 24 tiles"
    assert state.map.getHomeTile(TEST_TEAM) == None, "Team should not have a home tile assigned by default"

def test_assignOne():
    reimport(__name__)

    state = createTestInitState()
    entities = TEST_ENTITIES

    args = ActionAssignTileArgs(team=TEST_TEAM, index=1)
    action = ActionAssignTile(args=args, state=state, entities=entities)
    assert action.cost() == ActionCost(), "Assigning tile to team should be free"

    action.apply()
    tile = state.map.getHomeTile(TEST_TEAM)
    assert tile != None
    
    