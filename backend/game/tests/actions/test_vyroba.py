from decimal import Decimal

import pytest
from game.actions.actionBase import makeAction
from game.actions.common import ActionFailed
from game.actions.vyroba import ActionVyroba, ActionVyrobaArgs
from game.tests.actions.common import TEST_ENTITIES, TEAM_ADVANCED, createTestInitState
from game.tests.actions.test_armyDeploy import sendArmyTo

teamId = TEAM_ADVANCED


def test_initiate():
    entities = TEST_ENTITIES
    state = createTestInitState()
    team = state.teamStates[teamId]
    originalResources = team.resources.copy()

    args = ActionVyrobaArgs(
        vyroba = entities["vyr-drevo1Mat"],
        count = 1,
        tile = team.homeTile.entity,
        plunder = False,
        team = teamId
    )
    action = makeAction(ActionVyroba, state=state, entities=entities, args=args)

    result = action.applyInitiate()
    assert team.resources[entities["res-prace"]] == 90

    result = action.revertInitiate()
    assert team.resources[entities["res-prace"]] == 100

    args.count = 5
    action =  makeAction(ActionVyroba, state=state, entities=entities, args=args)

    result = action.applyInitiate()
    assert team.resources[entities["res-prace"]] == 50

    result = action.revertInitiate()
    assert team.resources[entities["res-prace"]] == 100

    args.vyroba = entities["vyr-drevo1Pro"]
    action =  makeAction(ActionVyroba, state=state, entities=entities, args=args)

    result = action.applyInitiate()
    assert team.resources[entities["res-prace"]] == 50
    assert team.resources[entities["res-obyvatel"]] == 90

    result = action.revertInitiate()
    assert team.resources[entities["res-obyvatel"]] == 100

    assert team.resources == originalResources


def test_simple():
    entities = TEST_ENTITIES
    state = createTestInitState()
    team = state.teamStates[teamId]
    team.resources[entities["pro-drevo"]] = 20
    originalResources = team.resources.copy()

    args = ActionVyrobaArgs(
        vyroba = entities["vyr-drevo1Mat"],
        count = 1,
        tile = team.homeTile.entity,
        plunder = False,
        team = teamId
    )
    action = makeAction(ActionVyroba, state=state, entities=entities, args=args)

    initResult = action.applyInitiate()
    commitResult = action.applyCommit(1, 5)

    assert team.resources == {entities["res-prace"]:80, entities["res-obyvatel"]:100, entities["pro-drevo"]: 20}
    assert "Vydejte týmu" in commitResult.message
    assert "Tým obdržel" in commitResult.message


def test_production():
    entities = TEST_ENTITIES
    state = createTestInitState()
    team = state.teamStates[teamId]
    team.resources[entities["pro-drevo"]] = 20

    args = ActionVyrobaArgs(
        vyroba = entities["vyr-drevo1Pro"],
        count = 1,
        tile = team.homeTile.entity,
        plunder = False,
        team = teamId
    )
    action = makeAction(ActionVyroba, state=state, entities=entities, args=args)

    initResult = action.applyInitiate()
    commitResult = action.applyCommit(1, 5)

    assert team.resources == {entities["res-prace"]:80, entities["res-obyvatel"]:98, entities["pro-drevo"]: 21}
    assert "Vydejte týmu" not in commitResult.message
    assert "Tým obdržel" in commitResult.message


def test_distance():
    entities = TEST_ENTITIES
    state = createTestInitState()
    team = state.teamStates[teamId]
    team.resources[entities["pro-drevo"]] = 20

    args = ActionVyrobaArgs(
        vyroba = entities["vyr-drevo1Mat"],
        count = 1,
        tile = entities["map-tile06"],
        plunder = False,
        team = teamId
    )
    action = makeAction(ActionVyroba, state=state, entities=entities, args=args)
    distance = action.requiresDelayedEffect()
    assert distance == 600


def test_richnessMaterial():
    entities = TEST_ENTITIES
    state = createTestInitState()
    team = state.teamStates[entities["tym-zluti"]]
    team.resources[entities["pro-drevo"]] = 20
    tile = state.map.tiles[27]
    sendArmyTo(entities, state, state.map.armies[3], tile.entity, equipment=8)
    
    args = ActionVyrobaArgs(
        vyroba = entities["vyr-drevoLes"],
        count = 2,
        tile = tile.entity,
        plunder = False,
        team = team.team
    )
    action = makeAction(ActionVyroba, state=state, entities=entities, args=args)

    initResult = action.applyInitiate()
    commitResult = action.applyCommit(1, 20)
    delayedResult = action.applyDelayedReward()

    assert team.resources == {entities["res-prace"]:70, entities["res-obyvatel"]:100, entities["pro-drevo"]: 20}
    assert "+80%" in delayedResult.message
    assert "[[mat-drevo|3]]" in delayedResult.message
    assert tile.richnessTokens == 8


def test_richnessProduction():
    entities = TEST_ENTITIES
    state = createTestInitState()
    team = state.teamStates[entities["tym-zluti"]]
    team.resources[entities["pro-drevo"]] = 20
    tile = state.map.tiles[27]
    sendArmyTo(entities, state, state.map.armies[3], tile.entity, equipment=8)
    
    args = ActionVyrobaArgs(
        vyroba = entities["vyr-drevoProdLes"],
        count = 2,
        tile = tile.entity,
        plunder = False,
        team = team.team
    )
    action = makeAction(ActionVyroba, state=state, entities=entities, args=args)

    initResult = action.applyInitiate()
    commitResult = action.applyCommit(1, 20)
    delayedResult = action.applyDelayedReward()

    assert team.resources == {entities["res-prace"]:70, entities["res-obyvatel"]:98, entities["pro-drevo"]: Decimal("23.6")}
    assert "+80%" in delayedResult.message
    assert "[[pro-drevo|3.6]]" in delayedResult.message
    assert tile.richnessTokens == 8


def test_plunderMaterial():
    entities = TEST_ENTITIES
    state = createTestInitState()
    team = state.teamStates[entities["tym-zluti"]]
    team.resources[entities["pro-drevo"]] = 20
    tile = state.map.tiles[27]
    sendArmyTo(entities, state, state.map.armies[3], tile.entity, equipment=8)
    
    args = ActionVyrobaArgs(
        vyroba = entities["vyr-drevoLes"],
        count = 2,
        tile = tile.entity,
        plunder = True,
        team = team.team
    )
    action = makeAction(ActionVyroba, state=state, entities=entities, args=args)

    initResult = action.applyInitiate()
    commitResult = action.applyCommit(1, 20)
    delayedResult = action.applyDelayedReward()

    assert team.resources == {entities["res-prace"]:70, entities["res-obyvatel"]:100, entities["pro-drevo"]: 20}
    assert "+80%" in delayedResult.message
    assert "[[mat-drevo|5]]" in delayedResult.message
    assert tile.richnessTokens == 6


def test_plunderProduction():
    entities = TEST_ENTITIES
    state = createTestInitState()
    team = state.teamStates[entities["tym-zluti"]]
    team.resources[entities["pro-drevo"]] = 20
    tile = state.map.tiles[27]
    sendArmyTo(entities, state, state.map.armies[3], tile.entity, equipment=8)

    args = ActionVyrobaArgs(
        vyroba = entities["vyr-drevoProdLes"],
        count = 4,
        tile = tile.entity,
        plunder = True,
        team = team.team
    )
    action = makeAction(ActionVyroba, state=state, entities=entities, args=args)

    initResult = action.applyInitiate()
    commitResult = action.applyCommit(1, 20)
    delayedResult = action.applyDelayedReward()

    assert team.resources == {entities["res-prace"]:50, entities["res-obyvatel"]:96, entities["pro-drevo"]: Decimal("31.2")}
    assert "+80%" in delayedResult.message
    assert "[[pro-drevo|11.2]]" in delayedResult.message
    assert tile.richnessTokens == 4


def test_featureMissing():
    entities = TEST_ENTITIES
    state = createTestInitState()
    team = state.teamStates[entities["tym-zluti"]]
    tile = state.map.tiles[27]
    team.resources[entities["pro-drevo"]] = 20
    
    args = ActionVyrobaArgs(
        vyroba = entities["vyr-drevoProdLes"],
        count = 2,
        tile = tile.entity,
        plunder = False,
        team = team.team
    )
    action = makeAction(ActionVyroba, state=state, entities=entities, args=args)

    initResult = action.applyInitiate()
    with pytest.raises(ActionFailed) as einfo:
        action.applyCommit(1, 100)
