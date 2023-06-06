import pytest

from game.actions.buildRoad import BuildRoadAction, BuildRoadArgs
from game.actions.common import ActionFailed
from game.state import ArmyGoal
from game.tests.actions.common import TEST_ENTITIES, createTestInitState
from game.tests.actions.test_armyDeploy import sendArmyTo


def test_buildRoad():
    entities = TEST_ENTITIES
    state = createTestInitState()
    team = entities.teams["tym-zluti"]
    tile = state.map.tiles[28]

    sendArmyTo(
        entities,
        state,
        state.map.armies[3],
        entities.tiles["map-tile28"],
        equipment=5,
        goal=ArmyGoal.Occupy,
    )

    action = BuildRoadAction.makeAction(
        state=state,
        entities=entities,
        args=BuildRoadArgs(team=team, tile=tile.entity),
    )
    commitResult = action.commitThrows(throws=1, dots=100)

    teamState = state.teamStates[team]
    assert teamState.roadsTo == set()

    assert len(commitResult.scheduledActions) == 1
    scheduled = commitResult.scheduledActions[0]
    delayedResult = scheduled.actionType.makeAction(
        state, entities, scheduled.args
    ).commit()

    assert teamState.roadsTo == set([tile.entity])


def test_unownedTile():
    entities = TEST_ENTITIES
    state = createTestInitState()
    team = entities.teams["tym-zluti"]
    tile = state.map.tiles[28]

    action = BuildRoadAction.makeAction(
        state=state,
        entities=entities,
        args=BuildRoadArgs(team=team, tile=tile.entity),
    )
    with pytest.raises(ActionFailed) as einfo:
        result = action.commitThrows(throws=0, dots=0)
