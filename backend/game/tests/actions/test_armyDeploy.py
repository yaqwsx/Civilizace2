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


def test_occupySelf():
    state = createTestInitState()
    entities = TEST_ENTITIES
    map = state.map
    armies = map.armies
    team = state.teamStates[entities["tym-ruzovi"]]
    army = armies[2]
    tile = entities["map-tile18"]

    sendArmyTo(entities, state, armies[18], entities["map-tile18"], equipment=4, goal=ArmyGoal.Occupy)
    result = sendArmyTo(entities, state, army, tile, equipment=20, goal=ArmyGoal.Occupy, boost=2)

    assert result.expected
    assert "posílila" in result.message
    assert "15." in result.message
    assert "|14]]" in result.message

    tile = state.map.tiles[18]
    assert state.map.getOccupyingArmy(tile.entity) == state.map.armies[18]
    exp = Army(index=2, team=team.team, name="A", equipment=0, level=3, tile=None, mode=ArmyMode.Idle)
    assert army == exp
    exp = Army(index=18, team=team.team, name="C", equipment=10, level=1, tile=state.map.tiles[18].entity, mode=ArmyMode.Occupying)
    assert state.map.armies[18] == exp


def test_replaceSelf():
    state = createTestInitState()
    entities = TEST_ENTITIES
    map = state.map
    armies = map.armies
    team = state.teamStates[entities["tym-ruzovi"]]
    army = armies[2]
    tile = entities["map-tile18"]

    sendArmyTo(entities, state, armies[18], entities["map-tile18"], equipment=9, goal=ArmyGoal.Occupy)
    result = sendArmyTo(entities, state, army, tile, equipment=15, goal=ArmyGoal.Replace, boost=2)

    assert result.expected
    assert "nahradila" in result.message
    assert "25" in result.message
    assert "|4]]" in result.message

    tile = state.map.tiles[18]
    assert state.map.getOccupyingArmy(tile.entity) == state.map.armies[2]
    exp = Army(index=2, team=team.team, name="A", equipment=20, level=3, tile=tile.entity, mode=ArmyMode.Occupying)
    assert army == exp
    exp = Army(index=18, team=team.team, name="C", equipment=0, level=1, tile=None, mode=ArmyMode.Idle)
    assert state.map.armies[18] == exp


def test_eliminateSelf():
    state = createTestInitState()
    entities = TEST_ENTITIES
    map = state.map
    armies = map.armies
    team = state.teamStates[entities["tym-ruzovi"]]
    army = armies[2]
    tile = entities["map-tile18"]

    sendArmyTo(entities, state, armies[18], entities["map-tile18"], equipment=9, goal=ArmyGoal.Occupy)
    result = sendArmyTo(entities, state, army, tile, equipment=15, goal=ArmyGoal.Eliminate, boost=2)

    assert result.expected
    assert "obsazeno" in result.message
    assert "|15]]" in result.message

    tile = state.map.tiles[18]
    assert state.map.getOccupyingArmy(tile.entity) == state.map.armies[18]
    exp = Army(index=2, team=team.team, name="A", equipment=0, level=3, tile=None, mode=ArmyMode.Idle)
    assert army == exp
    exp = Army(index=18, team=team.team, name="C", equipment=9, level=1, tile=state.map.tiles[18].entity, mode=ArmyMode.Occupying)
    assert state.map.armies[18] == exp


def test_supplySelf():
    state = createTestInitState()
    entities = TEST_ENTITIES
    map = state.map
    armies = map.armies
    team = state.teamStates[entities["tym-ruzovi"]]
    army = armies[2]
    tile = entities["map-tile18"]

    sendArmyTo(entities, state, armies[18], entities["map-tile18"], equipment=3, goal=ArmyGoal.Occupy)
    result = sendArmyTo(entities, state, army, tile, equipment=20, goal=ArmyGoal.Supply, boost=2)

    assert result.expected
    assert "posílila" in result.message
    assert "15." in result.message
    assert "|13]]" in result.message

    tile = state.map.tiles[18]
    assert state.map.getOccupyingArmy(tile.entity) == state.map.armies[18]
    exp = Army(index=2, team=team.team, name="A", equipment=0, level=3, tile=None, mode=ArmyMode.Idle)
    assert army == exp
    exp = Army(index=18, team=team.team, name="C", equipment=10, level=1, tile=state.map.tiles[18].entity, mode=ArmyMode.Occupying)
    assert state.map.armies[18] == exp


def test_occupyWin():
    state = createTestInitState()
    entities = TEST_ENTITIES
    map = state.map
    armies = map.armies
    team = state.teamStates[entities["tym-ruzovi"]]
    army = armies[2]
    tile = entities["map-tile18"]

    sendArmyTo(entities, state, armies[1], entities["map-tile18"], equipment=5, goal=ArmyGoal.Occupy)
    result = sendArmyTo(entities, state, army, tile, equipment=20, goal=ArmyGoal.Occupy)

    assert result.expected
    assert "obsadila" in result.message
    assert "23" in result.message

    tile = state.map.tiles[18]
    assert state.map.getOccupyingArmy(tile.entity) == state.map.armies[2]
    exp = Army(index=2, team=team.team, name="A", equipment=18, level=3, tile=state.map.tiles[18].entity, mode=ArmyMode.Occupying)
    assert army == exp
    exp = Army(index=1, team=entities["tym-cerveni"], name="A", equipment=0, level=3, tile=None, mode=ArmyMode.Idle)
    assert state.map.armies[1] == exp


def test_replaceWin():
    state = createTestInitState()
    entities = TEST_ENTITIES
    map = state.map
    armies = map.armies
    team = state.teamStates[entities["tym-ruzovi"]]
    army = armies[2]
    tile = entities["map-tile18"]

    sendArmyTo(entities, state, armies[1], entities["map-tile18"], equipment=5, goal=ArmyGoal.Occupy)
    result = sendArmyTo(entities, state, army, tile, equipment=20, goal=ArmyGoal.Replace)

    assert result.expected
    assert "obsadila" in result.message
    assert "23" in result.message

    tile = state.map.tiles[18]
    assert state.map.getOccupyingArmy(tile.entity) == state.map.armies[2]
    exp = Army(index=2, team=team.team, name="A", equipment=18, level=3, tile=state.map.tiles[18].entity, mode=ArmyMode.Occupying)
    assert army == exp
    exp = Army(index=1, team=entities["tym-cerveni"], name="A", equipment=0, level=3, tile=None, mode=ArmyMode.Idle)
    assert state.map.armies[1] == exp


def test_eliminateWin():
    state = createTestInitState()
    entities = TEST_ENTITIES
    map = state.map
    armies = map.armies
    team = state.teamStates[entities["tym-ruzovi"]]
    army = armies[2]
    tile = entities["map-tile18"]

    sendArmyTo(entities, state, armies[1], entities["map-tile18"], equipment=2, goal=ArmyGoal.Occupy)
    result = sendArmyTo(entities, state, army, tile, equipment=20, goal=ArmyGoal.Eliminate)

    assert result.expected
    assert "vyčistila" in result.message
    assert "20" in result.message

    tile = state.map.tiles[18]
    assert state.map.getOccupyingArmy(tile.entity) == None
    exp = Army(index=2, team=team.team, name="A", equipment=0, level=3, tile=None, mode=ArmyMode.Idle)
    assert army == exp
    exp = Army(index=1, team=entities["tym-cerveni"], name="A", equipment=0, level=3, tile=None, mode=ArmyMode.Idle)
    assert state.map.armies[1] == exp


def test_supplyRetreat():
    state = createTestInitState()
    entities = TEST_ENTITIES
    map = state.map
    armies = map.armies
    team = state.teamStates[entities["tym-ruzovi"]]
    army = armies[2]
    tile = entities["map-tile18"]

    sendArmyTo(entities, state, armies[1], entities["map-tile18"], equipment=5, goal=ArmyGoal.Occupy)
    result = sendArmyTo(entities, state, army, tile, equipment=20, goal=ArmyGoal.Supply)

    assert not result.expected
    assert " obsazeno nepřátelksou armádou." in result.message
    assert "|20]]" in result.message

    tile = state.map.tiles[18]
    assert state.map.getOccupyingArmy(tile.entity) == state.map.armies[1]
    exp = Army(index=2, team=team.team, name="A", equipment=0, level=3, tile=None, mode=ArmyMode.Idle)
    assert army == exp
    exp = Army(index=1, team=entities["tym-cerveni"], name="A", equipment=5, level=3, tile=state.map.tiles[18].entity, mode=ArmyMode.Occupying)
    assert state.map.armies[1] == exp


def test_occupyLose():
    state = createTestInitState()
    entities = TEST_ENTITIES
    map = state.map
    armies = map.armies
    team = state.teamStates[entities["tym-ruzovi"]]
    army = armies[2]
    tile = entities["map-tile18"]

    sendArmyTo(entities, state, armies[1], entities["map-tile18"], equipment=20, goal=ArmyGoal.Occupy)
    result = sendArmyTo(entities, state, army, tile, equipment=15, goal=ArmyGoal.Occupy)

    assert not result.expected
    assert "neuspěla" in result.message
    assert "|2]]" in result.message

    tile = state.map.tiles[18]
    assert state.map.getOccupyingArmy(tile.entity) == state.map.armies[1]
    exp = Army(index=2, team=team.team, name="A", equipment=0, level=3, tile=None, mode=ArmyMode.Idle)
    assert army == exp
    exp = Army(index=1, team=entities["tym-cerveni"], name="A", equipment=10, level=3, tile=state.map.tiles[18].entity, mode=ArmyMode.Occupying)
    assert state.map.armies[1] == exp


def test_replaceLose():
    state = createTestInitState()
    entities = TEST_ENTITIES
    map = state.map
    armies = map.armies
    team = state.teamStates[entities["tym-ruzovi"]]
    army = armies[2]
    tile = entities["map-tile18"]

    sendArmyTo(entities, state, armies[1], entities["map-tile18"], equipment=20, goal=ArmyGoal.Occupy)
    result = sendArmyTo(entities, state, army, tile, equipment=15, goal=ArmyGoal.Replace)

    assert not result.expected
    assert "neuspěla" in result.message
    assert "|2]]" in result.message

    tile = state.map.tiles[18]
    assert state.map.getOccupyingArmy(tile.entity) == state.map.armies[1]
    exp = Army(index=2, team=team.team, name="A", equipment=0, level=3, tile=None, mode=ArmyMode.Idle)
    assert army == exp
    exp = Army(index=1, team=entities["tym-cerveni"], name="A", equipment=10, level=3, tile=state.map.tiles[18].entity, mode=ArmyMode.Occupying)
    assert state.map.armies[1] == exp


def test_eliminateLose():
    state = createTestInitState()
    entities = TEST_ENTITIES
    map = state.map
    armies = map.armies
    team = state.teamStates[entities["tym-ruzovi"]]
    army = armies[2]
    tile = entities["map-tile18"]

    sendArmyTo(entities, state, armies[1], entities["map-tile18"], equipment=20, goal=ArmyGoal.Occupy)
    result = sendArmyTo(entities, state, army, tile, equipment=15, goal=ArmyGoal.Eliminate)

    assert not result.expected
    assert "neuspěla" in result.message
    assert "|2]]" in result.message

    tile = state.map.tiles[18]
    assert state.map.getOccupyingArmy(tile.entity) == state.map.armies[1]
    exp = Army(index=2, team=team.team, name="A", equipment=0, level=3, tile=None, mode=ArmyMode.Idle)
    assert army == exp
    exp = Army(index=1, team=entities["tym-cerveni"], name="A", equipment=10, level=3, tile=state.map.tiles[18].entity, mode=ArmyMode.Occupying)
    assert state.map.armies[1] == exp


def test_winReturnWeapons():
    state = createTestInitState()
    entities = TEST_ENTITIES
    map = state.map
    armies = map.armies
    team = state.teamStates[entities["tym-ruzovi"]]
    army = armies[2]
    tile = entities["map-tile18"]

    sendArmyTo(entities, state, armies[1], entities["map-tile18"], equipment=15, goal=ArmyGoal.Occupy)
    result = sendArmyTo(entities, state, army, tile, equipment=20, goal=ArmyGoal.Replace)

    assert result.expected
    assert "obsadila" in result.message
    assert "15" in result.message

    tile = state.map.tiles[18]
    assert state.map.getOccupyingArmy(tile.entity) == state.map.armies[2]
    exp = Army(index=2, team=team.team, name="A", equipment=10, level=3, tile=state.map.tiles[18].entity, mode=ArmyMode.Occupying)
    assert army == exp
    exp = Army(index=1, team=entities["tym-cerveni"], name="A", equipment=0, level=3, tile=None, mode=ArmyMode.Idle)
    assert state.map.armies[1] == exp
    assert "2 zbraní" in result.notifications[entities["tym-cerveni"]][0]