from game.tests.actions.common import TEAM_ADVANCED, TEST_ENTITIES, createTestInitState
from testing import reimport


def test_rawDistance():
    reimport(__name__)
    state = createTestInitState()

    expectations = [(5, 0), (4, 600), (3, 600), (7, 900), (2, 900)]

    for index, expected in expectations:
        distance = state.map.getRawDistance(
            TEAM_ADVANCED, state.map.tiles[index].entity
        )
        assert (
            distance == expected
        ), f"Raw distance of tile {index} does not match (exp={expected}, act={distance})"


def test_actualDistance():
    reimport(__name__)

    state = createTestInitState()

    expectations = [
        (1, 0, "Home tile"),
        # (0, 300, "Occupied tile"),
        (6, 300, "Road to tile"),
        # (3, 450, "Occupied distant tile"),
        (10, 450, "Road to distant tile"),
        (31, 480, "Around world"),
        # (30, 360, "Occupied around world"),
        (24, 360, "Road around world"),
        # (2, 0, "Road and occupied"),
    ]

    for index, expected, message in expectations:
        distance = state.map.getActualDistance(
            TEST_ENTITIES.teams["tym-modri"],
            state.map.tiles[index].entity,
            state.teamStates,
        )
        assert (
            distance == expected
        ), "Distance of tile {} does not match (exp={}, act={}): {}".format(
            index, expected, distance, message
        )


def test_reachableTiles():
    state = createTestInitState()
    entities = TEST_ENTITIES

    team = entities.teams["tym-zluti"]

    tiles = [x.entity for x in state.map.getReachableTiles(team)]

    assert len(tiles) == 11
    indexes = set([tile.index for tile in tiles])
    assert indexes == set([20, 26, 27, 28, 29, 30, 31, 2, 3, 4, 6])
