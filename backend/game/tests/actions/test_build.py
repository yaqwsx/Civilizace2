import pytest
from game.actions.build import BuildAction, BuildArgs
from game.actions.buildFinish import BuildFinishAction, BuildFinishArgs
from game.actions.common import ActionFailed
from game.tests.actions.common import TEST_ENTITIES, createTestInitState


def test_homeStart():
    entities = TEST_ENTITIES
    state = createTestInitState()
    building = entities["bui-pila"]
    team = entities["tym-zluti"]
    tile = state.map.tiles[29]

    action = BuildAction.makeAction(
        state=state,
        entities=entities,
        args=BuildArgs(building=building, team=team, tile=tile.entity),
    )
    action.applyCommit(1, 100)

    assert tile.buildings == set([building])


def test_homeFinish():
    entities = TEST_ENTITIES
    state = createTestInitState()
    building = entities["bui-pila"]
    team = entities["tym-zluti"]
    tile = state.map.tiles[29]

    action = BuildAction.makeAction(
        state=state,
        entities=entities,
        args=BuildArgs(building=building, team=team, tile=tile.entity),
    )
    action.applyCommit(1, 100)

    assert tile.buildings == set([building])


def test_failStartExisting():
    entities = TEST_ENTITIES
    state = createTestInitState()
    building = entities["bui-pila"]
    team = entities["tym-zluti"]
    tile = state.map.tiles[29]

    start = BuildAction.makeAction(
        state=state,
        entities=entities,
        args=BuildArgs(building=building, team=team, tile=tile.entity),
    )
    start.applyCommit(1, 100)

    finish = makeAction(
        BuildFinishAction,
        state=state,
        entities=entities,
        args=BuildFinishArgs(building=building, team=team, tile=tile.entity),
    )
    finish.applyCommit()

    with pytest.raises(ActionFailed) as einfo:
        start.applyCommit()


def test_buildOnOccupied():
    entities = TEST_ENTITIES
    state = createTestInitState()
    building = entities["bui-pila"]
    team = entities["tym-zluti"]
    tile = state.map.tiles[28]

    action = BuildAction.makeAction(
        state=state,
        entities=entities,
        args=BuildArgs(building=building, team=team, tile=tile.entity),
    )
    with pytest.raises(ActionFailed) as einfo:
        action.applyCommit()
