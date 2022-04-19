from decimal import Decimal
from game.state import ArmyId
from game.tests.actions.common import createTestInitStateWithHomeTiles
from testing import PYTEST_COLLECT, reimport

if not PYTEST_COLLECT:
    from game.tests.actions.common import TEST_ENTITIES, TEAM_ADVANCED

def test_rawDistance():
    reimport(__name__)

    state = createTestInitStateWithHomeTiles()

    expectations = [(1, 0), (0, 10), (31, 10), (3, 15), (30, 15)]

    for index, expected in expectations:
        distance = state.map.getRawDistance(TEAM_ADVANCED, state.map.tiles[index])
        assert distance == expected, "Raw distance of tile {index} does not match (exp={expected}, act={distance})"

def test_actualDistance():
    reimport(__name__)

    state = createTestInitStateWithHomeTiles()

    home = state.map.getHomeTile(TEAM_ADVANCED)
    home.roadsTo = [state.map.tiles[x].entity for x in [6, 10, 24, 2]]
    for x in [0, 3, 30,  2]:
        state.map.tiles[x].occupiedBy = ArmyId(prestige=10, team=TEAM_ADVANCED)

    expectations = [(1, 0, "Home tile"), 
                    (0, 5, "Occupied tile"),
                    (6, 5, "Road to tile"),
                    (3, Decimal(7.5), "Occupied distant tile"),
                    (10, Decimal(7.5), "Road to distant tile"),
                    (31, 8, "Around world"),
                    (30, 6, "Occupied around world"),
                    (24, 6, "Road around world"),
                    (2, 0, "Road and occupied")]

    for index, expected, message in expectations:
        distance = state.map.getActualDistance(TEAM_ADVANCED, state.map.tiles[index])
        assert distance == expected, "Distance of tile {} does not match (exp={}, act={}): {}"\
                                     .format(index, expected, distance, message)
