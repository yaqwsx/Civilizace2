import pytest
from game.actions.actionBase import makeAction
from game.actions.buildRoad import BuildRoadAction, BuildRoadArgs
from game.actions.common import ActionFailed
from game.state import ArmyGoal
from game.tests.actions.common import TEAM_BASIC, TEST_ENTITIES, createTestInitState
from game.tests.actions.test_armyDeploy import sendArmyTo


def test_buildRoad():
    entities = TEST_ENTITIES
    state = createTestInitState()
    team = entities["tym-zluti"]
    tile = state.map.tiles[28]

    sendArmyTo(entities, state, state.map.armies[3], entities["map-tile28"], equipment=5, goal=ArmyGoal.Occupy)

    action = makeAction(BuildRoadAction,
                        state=state, entities=entities, args=BuildRoadArgs(team=team, tile=tile.entity))
    action.applyCommit(1, 100)

    teamState = state.teamStates[team]
    assert teamState.roadsTo == set()

    action.applyDelayedReward()
    assert teamState.roadsTo == set([tile.entity])


def test_unownedTile():
    entities = TEST_ENTITIES
    state = createTestInitState()
    team = entities["tym-zluti"]
    tile = state.map.tiles[28]

    action = makeAction(BuildRoadAction,
                        state=state, entities=entities, args=BuildRoadArgs(team=team, tile=tile.entity))
    with pytest.raises(ActionFailed) as einfo:
        result = action.applyCommit()
