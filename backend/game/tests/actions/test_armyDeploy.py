from typing import NamedTuple

import pytest

from game.actions.armyDeploy import ArmyDeployAction, ArmyDeployArgs
from game.actions.armyRetreat import ArmyRetreatAction, ArmyRetreatArgs
from game.actions.common import ActionFailed
from game.entities import Entities, MapTileEntity, TeamEntity
from game.state import Army, ArmyGoal, ArmyMode, GameState
from game.tests.actions.common import TEAM_BASIC, TEST_ENTITIES, createTestInitState


def test_cost():
    state = createTestInitState()
    entities = TEST_ENTITIES
    armies = state.map.armies
    tiles = state.map.tiles
    armies[10].equipment = 5
    armies[18].equipment = 5
    armies[10].occupyTile(tiles[26].entity)
    armies[18].occupyTile(tiles[18].entity)

    teams = list(entities.teams.values())

    class TestArgs(NamedTuple):
        team: TeamEntity
        army: Army
        armyIndex: int
        tile: MapTileEntity
        expected_delay: int

    for test_args in [
        TestArgs(teams[0], state.map.armies[0], 2, entities.tiles["map-tile19"], 600),
        TestArgs(teams[0], state.map.armies[0], 2, entities.tiles["map-tile26"], 300),
    ]:
        args = ArmyDeployArgs(
            armyIndex=test_args.armyIndex,
            tile=test_args.tile,
            goal=ArmyGoal.Occupy,
            equipment=10,
            team=test_args.team,
            friendlyTeam=None,
        )
        action = ArmyDeployAction.makeAction(entities=entities, state=state, args=args)

        cost = action.cost()
        assert cost == {entities.zbrane: 10}, f"Requires {cost} (exp. 10x zbrane)"

        commitResult = action.commitSuccess()
        assert len(commitResult.scheduledActions) == 1
        scheduled = commitResult.scheduledActions[0]

        assert (
            scheduled.delay_s == test_args.expected_delay
        ), f"Deploying {test_args.army.name} to tile {test_args.tile.name} \
            should take {test_args.expected_delay}s, act={scheduled.delay_s})"


def test_commit():
    state = createTestInitState()
    entities = TEST_ENTITIES
    armyIndex = 0
    tile = entities.tiles["map-tile04"]
    teams = list(entities.teams.values())

    args = ArmyDeployArgs(
        armyIndex=armyIndex,
        tile=tile,
        goal=ArmyGoal.Occupy,
        equipment=10,
        team=teams[0],
        friendlyTeam=None,
    )
    action = ArmyDeployAction.makeAction(args=args, entities=entities, state=state)
    result = action.commitThrows(throws=0, dots=0)

    army = state.map.armies[armyIndex]
    exp = Army(
        index=armyIndex,
        name="A",
        team=teams[0],
        level=3,
        equipment=10,
        tile=tile,
        mode=ArmyMode.Marching,
        goal=ArmyGoal.Occupy,
    )
    assert (
        army == exp
    ), "Army in unexpected state:\n\nEXPECTED: {}\n\nACTUAL:  {}\n".format(exp, army)


def test_overequip():
    state = createTestInitState()
    entities = TEST_ENTITIES
    team = TEAM_BASIC
    armyIndex = 17
    tile = entities.tiles["map-tile04"]

    args = ArmyDeployArgs(
        armyIndex=armyIndex,
        tile=tile,
        team=team,
        goal=ArmyGoal.Occupy,
        equipment=11,
        friendlyTeam=None,
    )
    action = ArmyDeployAction.makeAction(args=args, entities=entities, state=state)
    with pytest.raises(ActionFailed) as einfo:
        action.cost()


def test_underequip():
    state = createTestInitState()
    entities = TEST_ENTITIES
    team = TEAM_BASIC
    armyIndex = 17
    tile = entities.tiles["map-tile04"]

    args = ArmyDeployArgs(
        armyIndex=armyIndex,
        tile=tile,
        team=team,
        goal=ArmyGoal.Occupy,
        equipment=0,
        friendlyTeam=None,
    )
    action = ArmyDeployAction.makeAction(args=args, entities=entities, state=state)
    with pytest.raises(ActionFailed) as einfo:
        action.cost()
        action.commitThrows(throws=0, dots=0)


def sendArmyTo(
    entities: Entities,
    state: GameState,
    army: Army,
    tile: MapTileEntity,
    goal: ArmyGoal = ArmyGoal.Occupy,
    equipment=0,
    boost=0,
    friendlyTeam=None,
):
    args = ArmyDeployArgs(
        armyIndex=army.index,
        tile=tile,
        team=army.team,
        goal=goal,
        equipment=equipment,
        friendlyTeam=friendlyTeam,
    )
    action = ArmyDeployAction.makeAction(args=args, entities=entities, state=state)
    commitResult = action.commitThrows(throws=0, dots=0)
    army.boost = boost

    assert len(commitResult.scheduledActions) == 1
    scheduled = commitResult.scheduledActions[0]
    return scheduled.actionType.makeAction(state, entities, scheduled.args).commit()


def test_occupyNobody():
    state = createTestInitState()
    entities = TEST_ENTITIES
    team = TEAM_BASIC
    armyIndex = 17
    army = state.map.armies[armyIndex]
    tile = entities.tiles["map-tile04"]

    result = sendArmyTo(entities, state, army, tile, equipment=8, boost=2)

    tile = state.map.tiles[4]
    assert state.map.getOccupyingArmy(entities.tiles["map-tile04"], state.teamStates) == army
    exp = Army(
        index=armyIndex,
        team=team,
        name="C",
        equipment=8,
        level=1,
        tile=tile.entity,
        mode=ArmyMode.Occupying,
    )
    assert army == exp
    assert result.expected
    assert "obsadil" in result.message


def test_replaceNobody():
    state = createTestInitState()
    entities = TEST_ENTITIES
    team = TEAM_BASIC
    armyIndex = 17
    army = state.map.armies[armyIndex]
    tile = entities.tiles["map-tile04"]

    result = sendArmyTo(
        entities, state, army, tile, equipment=8, goal=ArmyGoal.Replace, boost=2
    )

    tile = state.map.tiles[4]
    assert state.map.getOccupyingArmy(tile.entity, state.teamStates) == army
    exp = Army(
        index=armyIndex,
        team=team,
        name="C",
        equipment=8,
        level=1,
        tile=tile.entity,
        mode=ArmyMode.Occupying,
    )
    assert army == exp
    assert result.expected
    assert "obsadil" in result.message


def test_eliminateNobody():
    state = createTestInitState()
    entities = TEST_ENTITIES
    team = TEAM_BASIC
    armyIndex = 17
    army = state.map.armies[armyIndex]
    tile = entities.tiles["map-tile04"]

    result = sendArmyTo(
        entities, state, army, tile, equipment=8, goal=ArmyGoal.Eliminate, boost=2
    )

    tile = state.map.tiles[4]
    assert state.map.getOccupyingArmy(tile.entity, state.teamStates) is None
    exp = Army(
        index=armyIndex,
        team=team,
        name="C",
        equipment=0,
        level=1,
        tile=None,
        mode=ArmyMode.Idle,
    )
    assert army == exp
    assert result.expected
    assert "prázdné" in result.message


def test_supplyNobody():
    state = createTestInitState()
    entities = TEST_ENTITIES
    team = TEAM_BASIC
    armyIndex = 17
    army = state.map.armies[armyIndex]
    tile = entities.tiles["map-tile04"]

    result = sendArmyTo(
        entities, state, army, tile, equipment=8, goal=ArmyGoal.Supply, boost=2
    )

    tile = state.map.tiles[4]
    assert state.map.getOccupyingArmy(tile.entity, state.teamStates) is None
    exp = Army(
        index=armyIndex,
        team=team,
        name="C",
        equipment=0,
        level=1,
        tile=None,
        mode=ArmyMode.Idle,
    )
    assert army == exp
    assert result.expected
    assert "prázdné" in result.message


def test_occupySelf():
    state = createTestInitState()
    entities = TEST_ENTITIES
    map = state.map
    armies = map.armies
    team = state.teamStates[entities.teams["tym-ruzovi"]]
    army = armies[2]
    tile = entities.tiles["map-tile18"]

    sendArmyTo(
        entities,
        state,
        armies[18],
        entities.tiles["map-tile18"],
        equipment=4,
        goal=ArmyGoal.Occupy,
    )
    result = sendArmyTo(
        entities, state, army, tile, equipment=20, goal=ArmyGoal.Occupy, boost=2
    )

    assert result.expected
    assert "posílila" in result.message
    assert "15." in result.message
    assert "|14]]" in result.message

    tile = state.map.tiles[18]
    assert state.map.getOccupyingArmy(tile.entity, state.teamStates) == state.map.armies[18]
    exp = Army(
        index=2,
        team=team.team,
        name="A",
        equipment=0,
        level=3,
        tile=None,
        mode=ArmyMode.Idle,
    )
    assert army == exp
    exp = Army(
        index=18,
        team=team.team,
        name="C",
        equipment=10,
        level=1,
        tile=state.map.tiles[18].entity,
        mode=ArmyMode.Occupying,
    )
    assert state.map.armies[18] == exp


def test_replaceSelf():
    state = createTestInitState()
    entities = TEST_ENTITIES
    map = state.map
    armies = map.armies
    team = state.teamStates[entities.teams["tym-ruzovi"]]
    army = armies[2]
    tile = entities.tiles["map-tile18"]

    sendArmyTo(
        entities,
        state,
        armies[18],
        entities.tiles["map-tile18"],
        equipment=9,
        goal=ArmyGoal.Occupy,
    )
    result = sendArmyTo(
        entities, state, army, tile, equipment=15, goal=ArmyGoal.Replace, boost=2
    )

    assert result.expected
    assert "nahradila" in result.message
    assert "25" in result.message
    assert "|4]]" in result.message

    tile = state.map.tiles[18]
    assert state.map.getOccupyingArmy(tile.entity, state.teamStates) == state.map.armies[2]
    exp = Army(
        index=2,
        team=team.team,
        name="A",
        equipment=20,
        level=3,
        tile=tile.entity,
        mode=ArmyMode.Occupying,
    )
    assert army == exp
    exp = Army(
        index=18,
        team=team.team,
        name="C",
        equipment=0,
        level=1,
        tile=None,
        mode=ArmyMode.Idle,
    )
    assert state.map.armies[18] == exp


def test_eliminateSelf():
    state = createTestInitState()
    entities = TEST_ENTITIES
    map = state.map
    armies = map.armies
    team = state.teamStates[entities.teams["tym-ruzovi"]]
    army = armies[2]
    tile = entities.tiles["map-tile18"]

    sendArmyTo(
        entities,
        state,
        armies[18],
        entities.tiles["map-tile18"],
        equipment=9,
        goal=ArmyGoal.Occupy,
    )
    result = sendArmyTo(
        entities, state, army, tile, equipment=15, goal=ArmyGoal.Eliminate, boost=2
    )

    assert result.expected
    assert "obsazeno" in result.message
    assert "|15]]" in result.message

    tile = state.map.tiles[18]
    assert state.map.getOccupyingArmy(tile.entity, state.teamStates) == state.map.armies[18]
    exp = Army(
        index=2,
        team=team.team,
        name="A",
        equipment=0,
        level=3,
        tile=None,
        mode=ArmyMode.Idle,
    )
    assert army == exp
    exp = Army(
        index=18,
        team=team.team,
        name="C",
        equipment=9,
        level=1,
        tile=state.map.tiles[18].entity,
        mode=ArmyMode.Occupying,
    )
    assert state.map.armies[18] == exp


def test_supplySelf():
    state = createTestInitState()
    entities = TEST_ENTITIES
    map = state.map
    armies = map.armies
    team = state.teamStates[entities.teams["tym-ruzovi"]]
    army = armies[2]
    tile = entities.tiles["map-tile18"]

    sendArmyTo(
        entities,
        state,
        armies[18],
        entities.tiles["map-tile18"],
        equipment=3,
        goal=ArmyGoal.Occupy,
    )
    result = sendArmyTo(
        entities, state, army, tile, equipment=20, goal=ArmyGoal.Supply, boost=2
    )

    assert result.expected
    assert "posílila" in result.message
    assert "15." in result.message
    assert "|13]]" in result.message

    tile = state.map.tiles[18]
    assert state.map.getOccupyingArmy(tile.entity, state.teamStates) == state.map.armies[18]
    exp = Army(
        index=2,
        team=team.team,
        name="A",
        equipment=0,
        level=3,
        tile=None,
        mode=ArmyMode.Idle,
    )
    assert army == exp
    exp = Army(
        index=18,
        team=team.team,
        name="C",
        equipment=10,
        level=1,
        tile=state.map.tiles[18].entity,
        mode=ArmyMode.Occupying,
    )
    assert state.map.armies[18] == exp


def test_occupyWin():
    state = createTestInitState()
    entities = TEST_ENTITIES
    map = state.map
    armies = map.armies
    team = state.teamStates[entities.teams["tym-ruzovi"]]
    army = armies[2]
    tile = entities.tiles["map-tile18"]

    sendArmyTo(
        entities,
        state,
        armies[1],
        entities.tiles["map-tile18"],
        equipment=5,
        goal=ArmyGoal.Occupy,
    )
    result = sendArmyTo(entities, state, army, tile, equipment=20, goal=ArmyGoal.Occupy)

    assert result.expected
    assert "obsadila" in result.message
    assert "23" in result.message

    tile = state.map.tiles[18]
    assert state.map.getOccupyingArmy(tile.entity, state.teamStates) == state.map.armies[2]
    exp = Army(
        index=2,
        team=team.team,
        name="A",
        equipment=18,
        level=3,
        tile=state.map.tiles[18].entity,
        mode=ArmyMode.Occupying,
    )
    assert army == exp
    exp = Army(
        index=1,
        team=entities.teams["tym-cerveni"],
        name="A",
        equipment=0,
        level=3,
        tile=None,
        mode=ArmyMode.Idle,
    )
    assert state.map.armies[1] == exp


def test_replaceWin():
    state = createTestInitState()
    entities = TEST_ENTITIES
    map = state.map
    armies = map.armies
    team = state.teamStates[entities.teams["tym-ruzovi"]]
    army = armies[2]
    tile = entities.tiles["map-tile18"]

    sendArmyTo(
        entities,
        state,
        armies[1],
        entities.tiles["map-tile18"],
        equipment=5,
        goal=ArmyGoal.Occupy,
    )
    result = sendArmyTo(
        entities, state, army, tile, equipment=20, goal=ArmyGoal.Replace
    )

    assert result.expected
    assert "obsadila" in result.message
    assert "23" in result.message

    tile = state.map.tiles[18]
    assert state.map.getOccupyingArmy(tile.entity, state.teamStates) == state.map.armies[2]
    exp = Army(
        index=2,
        team=team.team,
        name="A",
        equipment=18,
        level=3,
        tile=state.map.tiles[18].entity,
        mode=ArmyMode.Occupying,
    )
    assert army == exp
    exp = Army(
        index=1,
        team=entities.teams["tym-cerveni"],
        name="A",
        equipment=0,
        level=3,
        tile=None,
        mode=ArmyMode.Idle,
    )
    assert state.map.armies[1] == exp


def test_eliminateWin():
    state = createTestInitState()
    entities = TEST_ENTITIES
    map = state.map
    armies = map.armies
    team = state.teamStates[entities.teams["tym-ruzovi"]]
    army = armies[2]
    tile = entities.tiles["map-tile18"]

    sendArmyTo(
        entities,
        state,
        armies[1],
        entities.tiles["map-tile18"],
        equipment=2,
        goal=ArmyGoal.Occupy,
    )
    result = sendArmyTo(
        entities, state, army, tile, equipment=20, goal=ArmyGoal.Eliminate
    )

    assert result.expected
    assert "vyčistila" in result.message
    assert "20" in result.message

    tile = state.map.tiles[18]
    assert state.map.getOccupyingArmy(tile.entity, state.teamStates) is None
    exp = Army(
        index=2,
        team=team.team,
        name="A",
        equipment=0,
        level=3,
        tile=None,
        mode=ArmyMode.Idle,
    )
    assert army == exp
    exp = Army(
        index=1,
        team=entities.teams["tym-cerveni"],
        name="A",
        equipment=0,
        level=3,
        tile=None,
        mode=ArmyMode.Idle,
    )
    assert state.map.armies[1] == exp


def test_supplyRetreat():
    state = createTestInitState()
    entities = TEST_ENTITIES
    map = state.map
    armies = map.armies
    team = state.teamStates[entities.teams["tym-ruzovi"]]
    army = armies[2]
    tile = entities.tiles["map-tile18"]

    sendArmyTo(
        entities,
        state,
        armies[1],
        entities.tiles["map-tile18"],
        equipment=5,
        goal=ArmyGoal.Occupy,
    )
    result = sendArmyTo(entities, state, army, tile, equipment=20, goal=ArmyGoal.Supply)

    assert not result.expected
    assert " obsazeno nepřátelksou armádou." in result.message
    assert "|20]]" in result.message

    tile = state.map.tiles[18]
    assert state.map.getOccupyingArmy(tile.entity, state.teamStates) == state.map.armies[1]
    exp = Army(
        index=2,
        team=team.team,
        name="A",
        equipment=0,
        level=3,
        tile=None,
        mode=ArmyMode.Idle,
    )
    assert army == exp
    exp = Army(
        index=1,
        team=entities.teams["tym-cerveni"],
        name="A",
        equipment=5,
        level=3,
        tile=state.map.tiles[18].entity,
        mode=ArmyMode.Occupying,
    )
    assert state.map.armies[1] == exp


def test_occupyLose():
    state = createTestInitState()
    entities = TEST_ENTITIES
    map = state.map
    armies = map.armies
    team = state.teamStates[entities.teams["tym-ruzovi"]]
    army = armies[2]
    tile = entities.tiles["map-tile18"]

    sendArmyTo(
        entities,
        state,
        armies[1],
        entities.tiles["map-tile18"],
        equipment=20,
        goal=ArmyGoal.Occupy,
    )
    result = sendArmyTo(entities, state, army, tile, equipment=15, goal=ArmyGoal.Occupy)

    assert not result.expected
    assert "neuspěla" in result.message
    assert "|2]]" in result.message

    tile = state.map.tiles[18]
    assert state.map.getOccupyingArmy(tile.entity, state.teamStates) == state.map.armies[1]
    exp = Army(
        index=2,
        team=team.team,
        name="A",
        equipment=0,
        level=3,
        tile=None,
        mode=ArmyMode.Idle,
    )
    assert army == exp
    exp = Army(
        index=1,
        team=entities.teams["tym-cerveni"],
        name="A",
        equipment=10,
        level=3,
        tile=state.map.tiles[18].entity,
        mode=ArmyMode.Occupying,
    )
    assert state.map.armies[1] == exp


def test_replaceLose():
    state = createTestInitState()
    entities = TEST_ENTITIES
    map = state.map
    armies = map.armies
    team = state.teamStates[entities.teams["tym-ruzovi"]]
    army = armies[2]
    tile = entities.tiles["map-tile18"]

    sendArmyTo(
        entities,
        state,
        armies[1],
        entities.tiles["map-tile18"],
        equipment=20,
        goal=ArmyGoal.Occupy,
    )
    result = sendArmyTo(
        entities, state, army, tile, equipment=15, goal=ArmyGoal.Replace
    )

    assert not result.expected
    assert "neuspěla" in result.message
    assert "|2]]" in result.message

    tile = state.map.tiles[18]
    assert state.map.getOccupyingArmy(tile.entity, state.teamStates) == state.map.armies[1]
    exp = Army(
        index=2,
        team=team.team,
        name="A",
        equipment=0,
        level=3,
        tile=None,
        mode=ArmyMode.Idle,
    )
    assert army == exp
    exp = Army(
        index=1,
        team=entities.teams["tym-cerveni"],
        name="A",
        equipment=10,
        level=3,
        tile=state.map.tiles[18].entity,
        mode=ArmyMode.Occupying,
    )
    assert state.map.armies[1] == exp


def test_eliminateLose():
    state = createTestInitState()
    entities = TEST_ENTITIES
    map = state.map
    armies = map.armies
    team = state.teamStates[entities.teams["tym-ruzovi"]]
    army = armies[2]
    tile = entities.tiles["map-tile18"]

    sendArmyTo(
        entities,
        state,
        armies[1],
        entities.tiles["map-tile18"],
        equipment=20,
        goal=ArmyGoal.Occupy,
    )
    result = sendArmyTo(
        entities, state, army, tile, equipment=15, goal=ArmyGoal.Eliminate
    )

    assert not result.expected
    assert "neuspěla" in result.message
    assert "|2]]" in result.message

    tile = state.map.tiles[18]
    assert state.map.getOccupyingArmy(tile.entity, state.teamStates) == state.map.armies[1]
    exp = Army(
        index=2,
        team=team.team,
        name="A",
        equipment=0,
        level=3,
        tile=None,
        mode=ArmyMode.Idle,
    )
    assert army == exp
    exp = Army(
        index=1,
        team=entities.teams["tym-cerveni"],
        name="A",
        equipment=10,
        level=3,
        tile=state.map.tiles[18].entity,
        mode=ArmyMode.Occupying,
    )
    assert state.map.armies[1] == exp


def test_winReturnWeapons():
    state = createTestInitState()
    entities = TEST_ENTITIES
    map = state.map
    armies = map.armies
    team = state.teamStates[entities.teams["tym-ruzovi"]]
    army = armies[2]
    tile = entities.tiles["map-tile18"]

    sendArmyTo(
        entities,
        state,
        armies[1],
        entities.tiles["map-tile18"],
        equipment=15,
        goal=ArmyGoal.Occupy,
    )
    result = sendArmyTo(
        entities, state, army, tile, equipment=20, goal=ArmyGoal.Replace
    )

    assert result.expected
    assert "obsadila" in result.message
    assert "15" in result.message

    tile = state.map.tiles[18]
    assert state.map.getOccupyingArmy(tile.entity, state.teamStates) == state.map.armies[2]
    exp = Army(
        index=2,
        team=team.team,
        name="A",
        equipment=10,
        level=3,
        tile=state.map.tiles[18].entity,
        mode=ArmyMode.Occupying,
    )
    assert army == exp
    exp = Army(
        index=1,
        team=entities.teams["tym-cerveni"],
        name="A",
        equipment=0,
        level=3,
        tile=None,
        mode=ArmyMode.Idle,
    )
    assert state.map.armies[1] == exp
    assert "2 zbraní" in result.notifications[entities.teams["tym-cerveni"]][0]


def test_retreatArmy():
    state = createTestInitState()
    entities = TEST_ENTITIES
    map = state.map
    armies = map.armies
    team = state.teamStates[entities.teams["tym-ruzovi"]]
    army = armies[2]
    tile = entities.tiles["map-tile18"]

    sendArmyTo(entities, state, armies[2], tile, equipment=15, goal=ArmyGoal.Occupy)

    args = ArmyRetreatArgs(armyIndex=army.index, team=army.team)
    action = ArmyRetreatAction.makeAction(args=args, entities=entities, state=state)
    result = action.commitThrows(throws=0, dots=0)

    assert map.getOccupyingArmy(tile, state.teamStates) is None

    exp = Army(
        index=2,
        team=team.team,
        name="A",
        equipment=0,
        level=3,
        tile=None,
        mode=ArmyMode.Idle,
    )
    assert army == exp
    assert "|15]]" in result.message


def test_supplyFriend():
    state = createTestInitState()
    entities = TEST_ENTITIES
    map = state.map
    armies = map.armies
    team = state.teamStates[entities.teams["tym-ruzovi"]]
    army = armies[2]
    tile = entities.tiles["map-tile18"]

    sendArmyTo(
        entities,
        state,
        armies[1],
        entities.tiles["map-tile18"],
        equipment=12,
        goal=ArmyGoal.Occupy,
    )
    result = sendArmyTo(
        entities,
        state,
        army,
        tile,
        equipment=19,
        goal=ArmyGoal.Supply,
        friendlyTeam=entities.teams["tym-cerveni"],
    )

    assert result.expected
    assert " armádu týmu " in result.message
    assert "o 8 " in result.message
    assert (
        "posílil vaši armádu A"
        in result.notifications[entities.teams["tym-cerveni"]][0]
    )

    tile = state.map.tiles[18]
    assert state.map.getOccupyingArmy(tile.entity, state.teamStates) == state.map.armies[1]
    exp = Army(
        index=2,
        team=team.team,
        name="A",
        equipment=0,
        level=3,
        tile=None,
        mode=ArmyMode.Idle,
    )
    assert army == exp
    exp = Army(
        index=1,
        team=entities.teams["tym-cerveni"],
        name="A",
        equipment=20,
        level=3,
        tile=state.map.tiles[18].entity,
        mode=ArmyMode.Occupying,
    )
    assert state.map.armies[1] == exp
