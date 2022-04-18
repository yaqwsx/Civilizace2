from game.tests.actions.common import createTestInitStateWithHomeTiles
from testing import PYTEST_COLLECT, reimport

if not PYTEST_COLLECT:
    from game.tests.actions.common import TEST_ENTITIES, TEST_TEAM

def test_rawDistance():
    reimport(__name__)

    state = createTestInitStateWithHomeTiles()

    expectations = [(1, 0), (0, 10), (31, 10), (3, 15), (30, 15)]

    for index, expected in expectations:
        distance = state.map.getRawDistance(TEST_TEAM, state.map.tiles[index])
        assert distance == expected, "Raw distance of tile {index} does not match (exp={expected}, act={distance})"


    