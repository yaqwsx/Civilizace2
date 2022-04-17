from game.actions.deployArmy import ActionDeployArmyArgs, ArmyDeploymentMode
from game.tests.actions.common import createTestInitState
from testing import PYTEST_COLLECT, reimport

if not PYTEST_COLLECT:
    from game.actions.nextTurn import ActionNextTurn, ActionNextTurnArgs
    from game.entities import Entities
    from game.state import GameState
    from game.tests.actions.common import TEST_ENTITIES


def test_initialState():
    reimport(__name__)

    state = createTestInitState()
    entities = TEST_ENTITIES
