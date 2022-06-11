# import pytest
# from game import state
# from game.actions.armyDeploy import ActionArmyDeploy, ArmyGoal
# from game.actions.common import ActionException, DebugException
# from game.state import Army, ArmyId, ArmyState
# from game.tests.actions.common import TEAM_ADVANCED, TEAM_BASIC
# from testing import PYTEST_COLLECT, reimport

# if not PYTEST_COLLECT:
#     from game.tests.actions.common import TEST_ENTITIES, createTestInitState
#     from game.actions.armyDeploy import ActionArmyDeployArgs, ArmyGoal

 
import pytest
from game.actions.ArmyDeploy import ActionArmyDeploy, ActionArmyDeployArgs
from game.actions.actionBase import makeAction
from game.actions.common import ActionFailed
from game.entities import Entities, MapTileEntity
from game.state import Army, ArmyGoal, ArmyMode, GameState, MapTile, StateModel
from game.tests.actions.common import TEAM_BASIC, TEST_ENTITIES, createTestInitState


def deployArmies(state: GameState, entities: Entities):
    armies = state.map.armies
    tiles = state.map.tiles
    armies[10].equipment = 5
    armies[18].equipment = 5
    state.map.occupyTile(armies[10], tiles[26])
    state.map.occupyTile(armies[18], tiles[18])
    

def test_cost():
    state = createTestInitState()
    entities = TEST_ENTITIES
    deployArmies(state, entities)

    teams = list(entities.teams.values())
    army = state.map.armies[0]
    tile = entities["map-tile19"]

    args = ActionArmyDeployArgs(armyIndex=2, tile=tile, goal=ArmyGoal.Occupy, equipment=10, team=teams[0])
    action = makeAction(ActionArmyDeploy, entities=entities, state=state, args=args)

    cost = action.cost()
    assert cost == {entities.zbrane: 10}, f"Requires {cost} (exp. 10x zbrane)"
    
    expected = 600
    assert action.requiresDelayedEffect() == expected, \
        f"Deploying {army.name} to tile {tile.name} \
        should take {expected}s, act={action.requiresDelayedEffect()})"

    args.tile = entities["map-tile26"]
    args.armyIndex = 2
    expected = 300
    assert action.requiresDelayedEffect() == expected, \
        f"Deploying {army.name} to tile {tile.name} \
        should take {expected}s, act={action.requiresDelayedEffect()})"
        


def test_commit():
    state = createTestInitState()
    entities = TEST_ENTITIES
    armyIndex = 0
    tile = entities["map-tile04"]
    teams = list(entities.teams.values())

    args = ActionArmyDeployArgs(armyIndex=armyIndex, tile=tile, goal=ArmyGoal.Occupy, equipment=10, team=teams[0])
    action = makeAction(ActionArmyDeploy, args=args, entities=entities, state=state)
    result = action.applyCommit()

    army = state.map.armies[armyIndex]
    exp = Army(index=armyIndex, name="A", team=teams[0], level=3, equipment=10, tile=tile, mode=ArmyMode.Marching, goal=ArmyGoal.Occupy)
    assert army == exp, "Army in unexpected state:\n\nEXPECTED: {}\n\nACTUAL:  {}\n".format(exp, army)


def test_overequip():

    state = createTestInitState()
    entities = TEST_ENTITIES
    team = TEAM_BASIC
    armyIndex = 17
    tile = entities["map-tile04"]

    args = ActionArmyDeployArgs(armyIndex=armyIndex, tile=tile, team=team, goal=ArmyGoal.Occupy, equipment=11)
    action = makeAction(ActionArmyDeploy, args=args, entities=entities, state=state)
    with pytest.raises(ActionFailed) as einfo:
        action.cost()


def test_underequip():

    state = createTestInitState()
    entities = TEST_ENTITIES
    team = TEAM_BASIC
    armyIndex = 17
    tile = entities["map-tile04"]

    args = ActionArmyDeployArgs(armyIndex=armyIndex, tile=tile, team=team, goal=ArmyGoal.Occupy, equipment=0)
    action = makeAction(ActionArmyDeploy, args=args, entities=entities, state=state)
    with pytest.raises(ActionFailed) as einfo:
        action.cost()
        action.applyCommit()

    

def sendArmyTo(entities: Entities, state: GameState, army: Army, tile: MapTileEntity, goal: ArmyGoal=ArmyGoal.Occupy, equipment=0, boost=0, friendlyTeam=None):
    args = ActionArmyDeployArgs(armyIndex=army.index, tile=tile, team=army.team, goal=goal, equipment=equipment, friendlyTeam=friendlyTeam)
    action = makeAction(ActionArmyDeploy, args=args, entities=entities, state=state)
    action.applyCommit()
    army.boost = boost
    return action.applyDelayedEffect()


def test_occupyNobody():
    state = createTestInitState()
    entities = TEST_ENTITIES
    team = TEAM_BASIC
    armyIndex = 17
    army = state.map.armies[armyIndex]
    tile = entities["map-tile04"]

    result = sendArmyTo(entities, state, army, tile, equipment=8, boost=2)

    tile = state.map.tiles[4]
    assert state.map.getOccupyingArmy(entities["map-tile04"]) == army
    exp = Army(index=armyIndex, team=team, name="C", equipment=8, level=1, tile=tile.entity, mode=ArmyMode.Occupying)
    assert army == exp
    assert result.expected
    assert "obsadil" in result.message


def test_replaceNobody():
    state = createTestInitState()
    entities = TEST_ENTITIES
    team = TEAM_BASIC
    armyIndex = 17
    army = state.map.armies[armyIndex]
    tile = entities["map-tile04"]

    result = sendArmyTo(entities, state, army, tile, equipment=8, goal=ArmyGoal.Replace, boost=2)

    tile = state.map.tiles[4]
    assert state.map.getOccupyingArmy(tile.entity) == army
    exp = Army(index=armyIndex, team=team, name="C", equipment=8, level=1, tile=tile.entity, mode=ArmyMode.Occupying)
    assert army == exp
    assert result.expected
    assert "obsadil" in result.message


def test_eliminateNobody():
    state = createTestInitState()
    entities = TEST_ENTITIES
    team = TEAM_BASIC
    armyIndex = 17
    army = state.map.armies[armyIndex]
    tile = entities["map-tile04"]

    result = sendArmyTo(entities, state, army, tile, equipment=8, goal=ArmyGoal.Eliminate, boost=2)

    tile = state.map.tiles[4]
    assert state.map.getOccupyingArmy(tile.entity) == None
    exp = Army(index=armyIndex, team=team, name="C", equipment=0, level=1, tile=None, mode=ArmyMode.Idle)
    assert army == exp
    assert result.expected
    assert "prázdné" in result.message


def test_supplyNobody():
    state = createTestInitState()
    entities = TEST_ENTITIES
    team = TEAM_BASIC
    armyIndex = 17
    army = state.map.armies[armyIndex]
    tile = entities["map-tile04"]

    result = sendArmyTo(entities, state, army, tile, equipment=8, goal=ArmyGoal.Supply, boost=2)

    tile = state.map.tiles[4]
    assert state.map.getOccupyingArmy(tile.entity) == None
    exp = Army(index=armyIndex, team=team, name="C", equipment=0, level=1, tile=None, mode=ArmyMode.Idle)
    assert army == exp
    assert result.expected
    assert "prázdné" in result.message


# def test_occupySelf():
#     reimport(__name__)
#     state = createTestInitState()
#     entities = TEST_ENTITIES
#     team = TEAM_BASIC
#     armyId = ArmyId(team=team, prestige=15)

#     sendArmyTo(entities, state, ArmyId(team=team, prestige=20), entities["map-tile04"], goal=ArmyGoal.Occupy, equipment=8, boost=2)
#     reward = sendArmyTo(entities, state, armyId, entities["map-tile04"], goal=ArmyGoal.Occupy, equipment=8, boost=2)

#     tile = state.map.tiles[4]
#     army15 = state.teamStates[team].armies[ArmyId(team=team, prestige=15)]
#     army20 = state.teamStates[team].armies[ArmyId(team=team, prestige=20)]
#     assert tile.occupiedBy == army20.id
#     exp = Army(team=team, equipment=15, tile=entities["map-tile04"], state=ArmyState.Occupying, prestige=20)
#     assert army20 == exp, "Army in unexpected state:\n\nEXPECTED: {}\n\nACTUAL:  {}\n".format(exp, army20)
#     exp = Army(team=team, equipment=0, tile=None, state=ArmyState.Idle, prestige=15)
#     assert army15 == exp, "Army in unexpected state:\n\nEXPECTED: {}\n\nACTUAL:  {}\n".format(exp, army15)
#     assert reward.reward == {entities.zbrane: 1}
#     assert reward.succeeded


# def test_replaceSelf():
#     reimport(__name__)
#     state = createTestInitState()
#     entities = TEST_ENTITIES
#     team = TEAM_BASIC

#     sendArmyTo(entities, state, ArmyId(team=team, prestige=20), entities["map-tile04"], goal=ArmyGoal.Occupy, equipment=8, boost=2)
#     reward = sendArmyTo(entities, state, ArmyId(team=team, prestige=15), entities["map-tile04"], goal=ArmyGoal.Replace, equipment=8)

#     tile = state.map.tiles[4]
#     army15 = state.teamStates[team].armies[ArmyId(team=team, prestige=15)]
#     army20 = state.teamStates[team].armies[ArmyId(team=team, prestige=20)]
#     assert tile.occupiedBy == army15.id
#     exp = Army(team=team, equipment=10, tile=entities["map-tile04"], state=ArmyState.Occupying, prestige=15)
#     assert army15 == exp, "Army in unexpected state:\n\nEXPECTED: {}\n\nACTUAL:  {}\n".format(exp, army15)
#     exp = Army(team=team, equipment=0, tile=None, state=ArmyState.Idle, prestige=20)
#     assert army20 == exp, "Army in unexpected state:\n\nEXPECTED: {}\n\nACTUAL:  {}\n".format(exp, army20)
#     assert reward.reward == {entities.zbrane: 6}
#     assert reward.succeeded


# def test_eliminateSelf():
#     reimport(__name__)
#     state = createTestInitState()
#     entities = TEST_ENTITIES
#     team = TEAM_BASIC
#     armyId = ArmyId(team=team, prestige=15)

#     sendArmyTo(entities, state, ArmyId(team=team, prestige=20), entities["map-tile04"], goal=ArmyGoal.Occupy, equipment=8, boost=2)
#     reward = sendArmyTo(entities, state, armyId, entities["map-tile04"], goal=ArmyGoal.Eliminate, equipment=8, boost=2)

#     tile = state.map.tiles[4]
#     army15 = state.teamStates[team].armies[ArmyId(team=team, prestige=15)]
#     army20 = state.teamStates[team].armies[ArmyId(team=team, prestige=20)]
#     assert tile.occupiedBy == army20.id
#     exp = Army(team=team, equipment=8, tile=entities["map-tile04"], state=ArmyState.Occupying, prestige=20)
#     assert army20 == exp, "Army in unexpected state:\n\nEXPECTED: {}\n\nACTUAL:  {}\n".format(exp, army20)
#     exp = Army(team=team, equipment=0, tile=None, state=ArmyState.Idle, prestige=15)
#     assert army15 == exp, "Army in unexpected state:\n\nEXPECTED: {}\n\nACTUAL:  {}\n".format(exp, army15)
#     assert reward.reward == {entities.zbrane: 8}
#     assert reward.succeeded


# def test_supportSelf():
#     reimport(__name__)
#     state = createTestInitState()
#     entities = TEST_ENTITIES
#     team = TEAM_BASIC

#     sendArmyTo(entities, state, ArmyId(team=team, prestige=20), entities["map-tile04"], goal=ArmyGoal.Occupy, equipment=8, boost=2)
#     reward = sendArmyTo(entities, state, ArmyId(team=team, prestige=15), entities["map-tile04"], goal=ArmyGoal.Supply, equipment=10)

#     tile = state.map.tiles[4]
#     army15 = state.teamStates[team].armies[ArmyId(team=team, prestige=15)]
#     army20 = state.teamStates[team].armies[ArmyId(team=team, prestige=20)]
#     assert tile.occupiedBy == army20.id
#     exp = Army(team=team, equipment=15, tile=entities["map-tile04"], state=ArmyState.Occupying, prestige=20)
#     assert army20 == exp, "Army in unexpected state:\n\nEXPECTED: {}\n\nACTUAL:  {}\n".format(exp, army20)
#     exp = Army(team=team, equipment=0, tile=None, state=ArmyState.Idle, prestige=15)
#     assert army15 == exp, "Army in unexpected state:\n\nEXPECTED: {}\n\nACTUAL:  {}\n".format(exp, army15)
#     assert reward.reward == {entities.zbrane: 3}
#     assert reward.succeeded


# def test_occupyWin():
#     reimport(__name__)
#     state = createTestInitState()
#     entities = TEST_ENTITIES
#     team = TEAM_BASIC
#     armyId = ArmyId(team=team, prestige=20)
#     tileId = entities["map-tile03"]

#     reward = sendArmyTo(entities, state, armyId, tileId, goal=ArmyGoal.Occupy, equipment=15)

#     tile = state.map.tiles[3]
#     defender = state.teamStates[TEAM_ADVANCED].armies[ArmyId(team=TEAM_ADVANCED, prestige=15)]
#     army = state.teamStates[team].armies[ArmyId(team=team, prestige=20)]

#     assert tile.occupiedBy == army.id
#     exp = Army(team=TEAM_ADVANCED, equipment=0, tile=None, state=ArmyState.Idle, prestige=15)
#     assert defender == exp, "Army in unexpected state:\n\nEXPECTED: {}\n\nACTUAL:  {}\n".format(exp, defender)
#     exp = Army(team=team, equipment=10, tile=tileId, state=ArmyState.Occupying, prestige=20)
#     assert army == exp, "Army in unexpected state:\n\nEXPECTED: {}\n\nACTUAL:  {}\n".format(exp, army)
#     assert reward.reward == {}
#     assert reward.succeeded


# def test_replaceWin():
#     reimport(__name__)
#     state = createTestInitState()
#     entities = TEST_ENTITIES
#     team = TEAM_BASIC
#     armyId = ArmyId(team=team, prestige=20)
#     tileId = entities["map-tile03"]
#     state.teamStates[TEAM_ADVANCED].armies[ArmyId(team=TEAM_ADVANCED, prestige=15)].boost = 5

#     reward = sendArmyTo(entities, state, armyId, tileId, goal=ArmyGoal.Replace, equipment=12, boost=5)

#     tile = state.map.tiles[3]
#     defender = state.teamStates[TEAM_ADVANCED].armies[ArmyId(team=TEAM_ADVANCED, prestige=15)]
#     army = state.teamStates[team].armies[ArmyId(team=team, prestige=20)]

#     assert tile.occupiedBy == army.id, "{}".format(reward)
#     exp = Army(team=TEAM_ADVANCED, equipment=0, tile=None, state=ArmyState.Idle, prestige=15)
#     assert defender == exp, "Army in unexpected state:\n\nEXPECTED: {}\n\nACTUAL:  {}\n".format(exp, defender)
#     exp = Army(team=team, equipment=2, tile=tileId, state=ArmyState.Occupying, prestige=20)
#     assert army == exp, "Army in unexpected state:\n\nEXPECTED: {}\n\nACTUAL:  {}\n".format(exp, army)
#     assert reward.reward == {}
#     assert reward.succeeded


# def test_eliminateWin():
#     reimport(__name__)
#     state = createTestInitState()
#     entities = TEST_ENTITIES
#     team = TEAM_BASIC
#     armyId = ArmyId(team=team, prestige=20)
#     tileId = entities["map-tile03"]
#     state.teamStates[TEAM_ADVANCED].armies[ArmyId(team=TEAM_ADVANCED, prestige=15)].boost = 1

#     reward = sendArmyTo(entities, state, armyId, tileId, goal=ArmyGoal.Eliminate, equipment=15, boost=5)

#     tile = state.map.tiles[3]
#     defender = state.teamStates[TEAM_ADVANCED].armies[ArmyId(team=TEAM_ADVANCED, prestige=15)]
#     army = state.teamStates[team].armies[ArmyId(team=team, prestige=20)]

#     assert tile.occupiedBy == None, "{}".format(reward)
#     exp = Army(team=TEAM_ADVANCED, equipment=0, tile=None, state=ArmyState.Idle, prestige=15)
#     assert defender == exp, "Army in unexpected state:\n\nEXPECTED: {}\n\nACTUAL:  {}\n".format(exp, defender)
#     exp = Army(team=team, equipment=0, tile=None, state=ArmyState.Idle, prestige=20)
#     assert army == exp, "Army in unexpected state:\n\nEXPECTED: {}\n\nACTUAL:  {}\n".format(exp, army)
#     assert reward.reward == {entities.zbrane: 9}
#     assert reward.succeeded


# def test_supplyRetreat():
#     reimport(__name__)
#     state = createTestInitState()
#     entities = TEST_ENTITIES
#     team = TEAM_BASIC
#     armyId = ArmyId(team=team, prestige=20)
#     tileId = entities["map-tile03"]

#     reward = sendArmyTo(entities, state, armyId, tileId, goal=ArmyGoal.Supply, equipment=15)

#     tile = state.map.tiles[3]
#     defender = state.teamStates[TEAM_ADVANCED].armies[ArmyId(team=TEAM_ADVANCED, prestige=15)]
#     army = state.teamStates[team].armies[ArmyId(team=team, prestige=20)]

#     assert tile.occupiedBy == defender.id
#     exp = Army(team=TEAM_ADVANCED, equipment=5, tile=tileId, state=ArmyState.Occupying, prestige=15)
#     assert defender == exp, "Army in unexpected state:\n\nEXPECTED: {}\n\nACTUAL:  {}\n".format(exp, defender)
#     exp = Army(team=team, equipment=0, tile=None, state=ArmyState.Idle, prestige=20)
#     assert army == exp, "Army in unexpected state:\n\nEXPECTED: {}\n\nACTUAL:  {}\n".format(exp, army)
#     assert reward.reward == {entities.zbrane: 15}
#     assert not reward.succeeded


# def test_occupyLose():
#     reimport(__name__)
#     state = createTestInitState()
#     entities = TEST_ENTITIES
#     team = TEAM_BASIC
#     armyId = ArmyId(team=team, prestige=20)
#     tileId = entities["map-tile02"]

#     reward = sendArmyTo(entities, state, armyId, tileId, goal=ArmyGoal.Occupy, equipment=15)

#     tile = state.map.tiles[2]
#     defender = state.teamStates[TEAM_ADVANCED].armies[ArmyId(team=TEAM_ADVANCED, prestige=25)]
#     army = state.teamStates[team].armies[ArmyId(team=team, prestige=20)]

#     assert tile.occupiedBy == defender.id
#     exp = Army(team=TEAM_ADVANCED, equipment=10, tile=tileId, state=ArmyState.Occupying, prestige=25)
#     assert defender == exp, "Army in unexpected state:\n\nEXPECTED: {}\n\nACTUAL:  {}\n".format(exp, defender)
#     exp = Army(team=team, equipment=0, tile=None, state=ArmyState.Idle, prestige=20)
#     assert army == exp, "Army in unexpected state:\n\nEXPECTED: {}\n\nACTUAL:  {}\n".format(exp, army)
#     assert reward.reward == {entities.zbrane: 2}
#     assert not reward.succeeded


# def test_replaceLose():
#     reimport(__name__)
#     state = createTestInitState()
#     entities = TEST_ENTITIES
#     team = TEAM_BASIC
#     armyId = ArmyId(team=team, prestige=20)
#     tileId = entities["map-tile02"]

#     reward = sendArmyTo(entities, state, armyId, tileId, goal=ArmyGoal.Replace, equipment=14, boost=2)

#     tile = state.map.tiles[2]
#     defender = state.teamStates[TEAM_ADVANCED].armies[ArmyId(team=TEAM_ADVANCED, prestige=25)]
#     army = state.teamStates[team].armies[ArmyId(team=team, prestige=20)]

#     assert tile.occupiedBy == defender.id
#     exp = Army(team=TEAM_ADVANCED, equipment=8, tile=tileId, state=ArmyState.Occupying, prestige=25)
#     assert defender == exp, "Army in unexpected state:\n\nEXPECTED: {}\n\nACTUAL:  {}\n".format(exp, defender)
#     exp = Army(team=team, equipment=0, tile=None, state=ArmyState.Idle, prestige=20)
#     assert army == exp, "Army in unexpected state:\n\nEXPECTED: {}\n\nACTUAL:  {}\n".format(exp, army)
#     assert reward.reward == {entities.zbrane: 1}
#     assert not reward.succeeded


# def test_eliminateLose():
#     reimport(__name__)
#     state = createTestInitState()
#     entities = TEST_ENTITIES
#     team = TEAM_BASIC
#     armyId = ArmyId(team=team, prestige=20)
#     tileId = entities["map-tile02"]

#     reward = sendArmyTo(entities, state, armyId, tileId, goal=ArmyGoal.Eliminate, equipment=10, boost=2)

#     tile = state.map.tiles[2]
#     defender = state.teamStates[TEAM_ADVANCED].armies[ArmyId(team=TEAM_ADVANCED, prestige=25)]
#     army = state.teamStates[team].armies[ArmyId(team=team, prestige=20)]

#     assert tile.occupiedBy == defender.id
#     exp = Army(team=TEAM_ADVANCED, equipment=10, tile=tileId, state=ArmyState.Occupying, prestige=25)
#     assert defender == exp, "Army in unexpected state:\n\nEXPECTED: {}\n\nACTUAL:  {}\n".format(exp, defender)
#     exp = Army(team=team, equipment=0, tile=None, state=ArmyState.Idle, prestige=20)
#     assert army == exp, "Army in unexpected state:\n\nEXPECTED: {}\n\nACTUAL:  {}\n".format(exp, army)
#     assert reward.reward == {entities.zbrane: 0}
#     assert not reward.succeeded


# def test_supplyFriend():
#     reimport(__name__)
#     state = createTestInitState()
#     entities = TEST_ENTITIES
#     team = TEAM_BASIC
#     armyId = ArmyId(team=team, prestige=20)
#     tileId = entities["map-tile03"]

#     reward = sendArmyTo(entities, state, armyId, tileId, goal=ArmyGoal.Supply, equipment=5, boost=2, friendlyTeam=TEAM_ADVANCED)

#     tile = state.map.tiles[3]
#     defender = state.teamStates[TEAM_ADVANCED].armies[ArmyId(team=TEAM_ADVANCED, prestige=15)]
#     army = state.teamStates[team].armies[ArmyId(team=team, prestige=20)]

#     assert tile.occupiedBy == defender.id
#     exp = Army(team=TEAM_ADVANCED, equipment=10, tile=tileId, state=ArmyState.Occupying, prestige=15)
#     assert defender == exp, "Army in unexpected state:\n\nEXPECTED: {}\n\nACTUAL:  {}\n".format(exp, defender)
#     exp = Army(team=team, equipment=0, tile=None, state=ArmyState.Idle, prestige=20)
#     assert army == exp, "Army in unexpected state:\n\nEXPECTED: {}\n\nACTUAL:  {}\n".format(exp, army)
#     assert reward.reward == {entities.zbrane: 0}
#     assert reward.succeeded
