import pytest
from game import state
from game.actions.armyDeploy import ActionArmyDeploy, ArmyGoal
from game.actions.common import ActionException
from game.state import Army, ArmyId, ArmyState
from game.tests.actions.common import TEAM_BASIC
from testing import PYTEST_COLLECT, reimport

if not PYTEST_COLLECT:
    from game.tests.actions.common import TEST_ENTITIES, createTestInitState
    from game.actions.armyDeploy import ActionArmyDeployArgs, ArmyGoal


def test_cost():
    reimport(__name__)

    state = createTestInitState()
    entities = TEST_ENTITIES

    team = TEAM_BASIC
    armyId = ArmyId(team=team, prestige=15)
    tile = entities["map-tile04"]

    args = ActionArmyDeployArgs(army=armyId, tile=tile, team=team, goal=ArmyGoal.Occupy, equipment=10)
    action = ActionArmyDeploy(args=args, entities=entities, state=state)

    cost = action.cost()
    assert cost.resources == {entities.zbrane: 10}, "Requires {} (exp. {})".format(cost.resources, entities.zbrane)
    assert cost.postpone == 10, "Deploying {} to tile {} should take 10 minutes (act={})"\
        .format(armyId, tile, cost.postpone)
    

def test_commit():
    reimport(__name__)

    state = createTestInitState()
    entities = TEST_ENTITIES
    team = TEAM_BASIC
    armyId = ArmyId(team=team, prestige=15)
    tile = entities["map-tile04"]

    args = ActionArmyDeployArgs(army=armyId, tile=tile, team=team, goal=ArmyGoal.Occupy, equipment=10)
    action = ActionArmyDeploy(args=args, entities=entities, state=state)
    result = action.commit()

    army = state.teamStates[team].armies[armyId]
    exp = Army(team=team, prestige=15, equipment=10, tile=tile, state=ArmyState.Marching, goal=ArmyGoal.Occupy)
    assert army == exp, "Army in unexpected state:\n\nEXPECTED: {}\n\nACTUAL:  {}\n".format(exp, army)
    assert result.reward == {}


def test_invalidArgs():
    reimport(__name__)

    state = createTestInitState()
    entities = TEST_ENTITIES
    team = TEAM_BASIC
    armyId = ArmyId(team=team, prestige=15)
    tile = entities["map-tile04"]

    args = ActionArmyDeployArgs(army=armyId, tile=tile, team=team, goal=ArmyGoal.Occupy, equipment=11)
    action = ActionArmyDeploy(args=args, entities=entities, state=state)
    with pytest.raises(ActionException) as einfo:
        action.cost()
        action.commit()

    args = ActionArmyDeployArgs(army=armyId, tile=tile, team=team, goal=ArmyGoal.Occupy, equipment=-1)
    action = ActionArmyDeploy(args=args, entities=entities, state=state)
    with pytest.raises(ActionException) as einfo:
        action.cost()
        action.commit()


def sendArmyTo(entities, state, army, tile, goal=ArmyGoal.Occupy, equipment=0, boost=0):
    args = ActionArmyDeployArgs(army=army, tile=tile, team=army.team, goal=goal, equipment=equipment)
    action = ActionArmyDeploy(args=args, entities=entities, state=state)
    action.commit()
    state.teamStates[army.team].armies[army].boost = boost
    return action.delayed()


def test_occupyNobody():
    reimport(__name__)

    state = createTestInitState()
    entities = TEST_ENTITIES
    team = TEAM_BASIC
    armyId = ArmyId(team=team, prestige=15)

    reward = sendArmyTo(entities, state, armyId, entities["map-tile04"], equipment=8, boost=2)

    tile = state.map.tiles[4]
    army = state.teamStates[team].armies[armyId]
    assert tile.occupiedBy == armyId
    exp = Army(team=team, equipment=8, tile=tile.entity, state=ArmyState.Occupying, prestige=15)
    assert army == exp
    assert reward.reward == {}
    assert reward.succeeded


def test_replaceNobody():
    reimport(__name__)
    state = createTestInitState()
    entities = TEST_ENTITIES
    team = TEAM_BASIC

    reward = sendArmyTo(entities, state, ArmyId(team=team, prestige=15), entities["map-tile04"], goal=ArmyGoal.Replace, equipment=8, boost=2)

    tile = state.map.tiles[4]
    army = state.teamStates[team].armies[ArmyId(team=team, prestige=15)]
    assert tile.occupiedBy == army.id
    exp = Army(team=team, equipment=8, tile=entities["map-tile04"], state=ArmyState.Occupying, prestige=15)
    assert army == exp
    assert reward.reward == {}
    assert reward.succeeded


def test_eliminateNobody():
    reimport(__name__)
    state = createTestInitState()
    entities = TEST_ENTITIES
    team = TEAM_BASIC
    armyId = ArmyId(team=team, prestige=15)

    reward = sendArmyTo(entities, state, armyId, entities["map-tile04"], goal=ArmyGoal.Eliminate, equipment=8, boost=2)

    tile = state.map.tiles[4]
    army = state.teamStates[team].armies[armyId]
    assert tile.occupiedBy == None
    exp = Army(team=team, equipment=0, tile=None, state=ArmyState.Idle, prestige=15)
    assert army == exp, "Army in unexpected state:\n\nEXPECTED: {}\n\nACTUAL:  {}\n".format(exp, army)
    assert reward.reward == {entities.zbrane: 8}
    assert reward.succeeded


def test_supportNobody():
    reimport(__name__)
    state = createTestInitState()
    entities = TEST_ENTITIES
    team = TEAM_BASIC

    reward = sendArmyTo(entities, state, ArmyId(team=team, prestige=15), entities["map-tile04"], goal=ArmyGoal.Support, equipment=8, boost=2)

    tile = state.map.tiles[4]
    army = state.teamStates[team].armies[ArmyId(team=team, prestige=15)]
    assert tile.occupiedBy == None
    exp = Army(team=team, equipment=0, tile=None, state=ArmyState.Idle, prestige=15)
    assert army == exp
    assert reward.reward == {entities.zbrane: 8}
    assert reward.succeeded


def test_occupySelf():
    reimport(__name__)
    state = createTestInitState()
    entities = TEST_ENTITIES
    team = TEAM_BASIC
    armyId = ArmyId(team=team, prestige=15)

    sendArmyTo(entities, state, ArmyId(team=team, prestige=20), entities["map-tile04"], goal=ArmyGoal.Occupy, equipment=8, boost=2)
    reward = sendArmyTo(entities, state, armyId, entities["map-tile04"], goal=ArmyGoal.Occupy, equipment=8, boost=2)

    tile = state.map.tiles[4]
    army15 = state.teamStates[team].armies[ArmyId(team=team, prestige=15)]
    army20 = state.teamStates[team].armies[ArmyId(team=team, prestige=20)]
    assert tile.occupiedBy == army20.id
    exp = Army(team=team, equipment=15, tile=entities["map-tile04"], state=ArmyState.Occupying, prestige=20)
    assert army20 == exp, "Army in unexpected state:\n\nEXPECTED: {}\n\nACTUAL:  {}\n".format(exp, army20)
    exp = Army(team=team, equipment=0, tile=None, state=ArmyState.Idle, prestige=15)
    assert army15 == exp, "Army in unexpected state:\n\nEXPECTED: {}\n\nACTUAL:  {}\n".format(exp, army15)
    assert reward.reward == {entities.zbrane: 1}
    assert reward.succeeded


def test_replaceSelf():
    reimport(__name__)
    state = createTestInitState()
    entities = TEST_ENTITIES
    team = TEAM_BASIC

    sendArmyTo(entities, state, ArmyId(team=team, prestige=20), entities["map-tile04"], goal=ArmyGoal.Occupy, equipment=8, boost=2)
    reward = sendArmyTo(entities, state, ArmyId(team=team, prestige=15), entities["map-tile04"], goal=ArmyGoal.Replace, equipment=8)

    tile = state.map.tiles[4]
    army15 = state.teamStates[team].armies[ArmyId(team=team, prestige=15)]
    army20 = state.teamStates[team].armies[ArmyId(team=team, prestige=20)]
    assert tile.occupiedBy == army15.id
    exp = Army(team=team, equipment=10, tile=entities["map-tile04"], state=ArmyState.Occupying, prestige=15)
    assert army15 == exp, "Army in unexpected state:\n\nEXPECTED: {}\n\nACTUAL:  {}\n".format(exp, army15)
    exp = Army(team=team, equipment=0, tile=None, state=ArmyState.Idle, prestige=20)
    assert army20 == exp, "Army in unexpected state:\n\nEXPECTED: {}\n\nACTUAL:  {}\n".format(exp, army20)
    assert reward.reward == {entities.zbrane: 6}
    assert reward.succeeded


def test_eliminateSelf():
    reimport(__name__)
    state = createTestInitState()
    entities = TEST_ENTITIES
    team = TEAM_BASIC
    armyId = ArmyId(team=team, prestige=15)

    sendArmyTo(entities, state, ArmyId(team=team, prestige=20), entities["map-tile04"], goal=ArmyGoal.Occupy, equipment=8, boost=2)
    reward = sendArmyTo(entities, state, armyId, entities["map-tile04"], goal=ArmyGoal.Eliminate, equipment=8, boost=2)

    tile = state.map.tiles[4]
    army15 = state.teamStates[team].armies[ArmyId(team=team, prestige=15)]
    army20 = state.teamStates[team].armies[ArmyId(team=team, prestige=20)]
    assert tile.occupiedBy == army20.id
    exp = Army(team=team, equipment=8, tile=entities["map-tile04"], state=ArmyState.Occupying, prestige=20)
    assert army20 == exp, "Army in unexpected state:\n\nEXPECTED: {}\n\nACTUAL:  {}\n".format(exp, army20)
    exp = Army(team=team, equipment=0, tile=None, state=ArmyState.Idle, prestige=15)
    assert army15 == exp, "Army in unexpected state:\n\nEXPECTED: {}\n\nACTUAL:  {}\n".format(exp, army15)
    assert reward.reward == {entities.zbrane: 8}
    assert reward.succeeded


def test_supportSelf():
    reimport(__name__)
    state = createTestInitState()
    entities = TEST_ENTITIES
    team = TEAM_BASIC

    sendArmyTo(entities, state, ArmyId(team=team, prestige=20), entities["map-tile04"], goal=ArmyGoal.Occupy, equipment=8, boost=2)
    reward = sendArmyTo(entities, state, ArmyId(team=team, prestige=15), entities["map-tile04"], goal=ArmyGoal.Support, equipment=10)

    tile = state.map.tiles[4]
    army15 = state.teamStates[team].armies[ArmyId(team=team, prestige=15)]
    army20 = state.teamStates[team].armies[ArmyId(team=team, prestige=20)]
    assert tile.occupiedBy == army20.id
    exp = Army(team=team, equipment=15, tile=entities["map-tile04"], state=ArmyState.Occupying, prestige=20)
    assert army20 == exp, "Army in unexpected state:\n\nEXPECTED: {}\n\nACTUAL:  {}\n".format(exp, army20)
    exp = Army(team=team, equipment=0, tile=None, state=ArmyState.Idle, prestige=15)
    assert army15 == exp, "Army in unexpected state:\n\nEXPECTED: {}\n\nACTUAL:  {}\n".format(exp, army15)
    assert reward.reward == {entities.zbrane: 3}
    assert reward.succeeded