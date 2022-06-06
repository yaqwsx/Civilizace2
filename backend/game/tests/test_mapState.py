from decimal import Decimal
from game.state import ArmyId
from game.tests.actions.common import createTestInitState
from testing import PYTEST_COLLECT, reimport

if not PYTEST_COLLECT:
    from game.tests.actions.common import TEST_ENTITIES, TEAM_ADVANCED

def test_rawDistance():
    reimport(__name__)

    state = createTestInitState()

    expectations = [(5, 0), (4, 600), (3, 600), (7, 900), (2, 900)]

    for index, expected in expectations:
        distance = state.map.getRawDistance(TEAM_ADVANCED, state.map.tiles[index].entity)
        assert distance == expected, f"Raw distance of tile {index} does not match (exp={expected}, act={distance})"

def test_actualDistance():
    reimport(__name__)

    state = createTestInitState()

    expectations = [(1, 0, "Home tile"), 
#                    (0, 300, "Occupied tile"),
                    (6, 300, "Road to tile"),
#                    (3, 450, "Occupied distant tile"),
                    (10, 450, "Road to distant tile"),
                    (31, 480, "Around world"),
#                    (30, 360, "Occupied around world"),
                    (24, 360, "Road around world"),
#                    (2, 0, "Road and occupied")]
    ]

    for index, expected, message in expectations:
        distance = state.map.getActualDistance(TEST_ENTITIES["tym-modri"], state.map.tiles[index].entity)
        assert distance == expected, "Distance of tile {} does not match (exp={}, act={}): {}"\
                                     .format(index, expected, distance, message)
