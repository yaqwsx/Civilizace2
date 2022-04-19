from testing import PYTEST_COLLECT, reimport

if not PYTEST_COLLECT:
    from game.entities import Entities
    from game.state import GameState
    from game.tests.actions.common import TEST_ENTITIES, createTestInitState
    from game.actions.armyDeploy import ActionArmyDeployArgs, ArmyGoal


def test_initialState():
    reimport(__name__)

    state = createTestInitState()
    entities = TEST_ENTITIES
