import pytest
from game.actions.actionBase import makeAction
from game.actions.build import ActionBuild, ActionBuildArgs
from game.actions.buildFinish import ActionBuildFinish, ActionBuildFinishArgs
from game.actions.common import ActionFailed
from game.tests.actions.common import TEAM_BASIC, TEST_ENTITIES, createTestInitState


def test_homeStart():
    entities = TEST_ENTITIES
    state = createTestInitState()
    building = entities["bui-pila"]
    team = entities["tym-zluti"]
    tile = state.map.tiles[29]

    action = makeAction(ActionBuild,
        state=state, entities=entities, args=ActionBuildArgs(build=building, team=team, tile=tile.entity))
    action.applyCommit(1, 100)

    assert tile.unfinished.get(team) == set([building])


def test_homeFinish():
    entities = TEST_ENTITIES
    state = createTestInitState()
    building = entities["bui-pila"]
    team = entities["tym-zluti"]
    tile = state.map.tiles[29]

    action = makeAction(ActionBuild,
        state=state, entities=entities, args=ActionBuildArgs(build=building, team=team, tile=tile.entity))
    action.applyCommit(1, 100)

    assert tile.unfinished.get(team) == set([building])

    action = makeAction(ActionBuildFinish,
        state=state, entities=entities, args=ActionBuildFinishArgs(build=building, team=team, tile=tile.entity))
    action.applyCommit()

    assert tile.unfinished.get(team) == set()
    assert tile.buildings == set([building])

    result = action.applyCommit()
    assert not result.expected


def test_failStartExisting():
    entities = TEST_ENTITIES
    state = createTestInitState()
    building = entities["bui-pila"]
    team = entities["tym-zluti"]
    tile = state.map.tiles[29]

    start = makeAction(ActionBuild,
        state=state, entities=entities, args=ActionBuildArgs(build=building, team=team, tile=tile.entity))
    start.applyCommit(1, 100)

    finish = makeAction(ActionBuildFinish,
        state=state, entities=entities, args=ActionBuildFinishArgs(build=building, team=team, tile=tile.entity))
    finish.applyCommit()

    with pytest.raises(ActionFailed) as einfo:
        start.applyCommit()

