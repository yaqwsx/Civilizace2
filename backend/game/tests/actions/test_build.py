import pytest

from game.actions.build import BuildAction, BuildArgs
from game.actions.common import ActionFailed
from game.tests.actions.common import TEST_ENTITIES, createTestInitState


def test_homeStart():
    entities = TEST_ENTITIES
    state = createTestInitState()
    building = entities.buildings["bui-pila"]
    team = entities.teams["tym-zluti"]
    tile = state.map.tiles[29]

    action = BuildAction.makeAction(
        state=state,
        entities=entities,
        args=BuildArgs(building=building, team=team, tile=tile.entity),
    )
    action.commitThrows(throws=1, dots=100)

    assert tile.buildings == set([building])


def test_homeFinish():
    entities = TEST_ENTITIES
    state = createTestInitState()
    building = entities.buildings["bui-pila"]
    team = entities.teams["tym-zluti"]
    tile = state.map.tiles[29]

    action = BuildAction.makeAction(
        state=state,
        entities=entities,
        args=BuildArgs(building=building, team=team, tile=tile.entity),
    )
    action.commitThrows(throws=1, dots=100)

    assert tile.buildings == set([building])


def test_failStartExisting():
    entities = TEST_ENTITIES
    state = createTestInitState()
    building = entities.buildings["bui-pila"]
    team = entities.teams["tym-zluti"]
    tile = state.map.tiles[29]

    start = BuildAction.makeAction(
        state=state,
        entities=entities,
        args=BuildArgs(building=building, team=team, tile=tile.entity),
    )
    start.commitThrows(throws=1, dots=100)

    with pytest.raises(ActionFailed) as einfo:
        start.commitThrows(throws=0, dots=0)


def test_buildOnOccupied():
    entities = TEST_ENTITIES
    state = createTestInitState()
    building = entities.buildings["bui-pila"]
    team = entities.teams["tym-zluti"]
    tile = state.map.tiles[28]

    action = BuildAction.makeAction(
        state=state,
        entities=entities,
        args=BuildArgs(building=building, team=team, tile=tile.entity),
    )
    with pytest.raises(ActionFailed) as einfo:
        action.commitThrows(throws=0, dots=0)
