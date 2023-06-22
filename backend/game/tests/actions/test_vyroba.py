from decimal import Decimal

import pytest

from game.actions.common import ActionFailed
from game.actions.vyroba import VyrobaAction, VyrobaArgs
from game.tests.actions.common import TEAM_ADVANCED, TEST_ENTITIES, createTestInitState
from game.tests.actions.test_armyDeploy import sendArmyTo

teamEntity = TEAM_ADVANCED


def test_initiate():
    entities = TEST_ENTITIES
    state = createTestInitState()
    team = state.teamStates[teamEntity]
    originalResources = team.resources.copy()

    args = VyrobaArgs(
        vyroba=entities.vyrobas["vyr-drevo1Mat"],
        count=1,
        tile=team.homeTile.entity,
        team=teamEntity,
    )
    action = VyrobaAction.makeAction(state=state, entities=entities, args=args)

    result = action.applyInitiate()
    assert team.resources[entities.work] == 90

    result = action.revertInitiate()
    assert team.resources[entities.work] == 100

    args.count = 5
    action = VyrobaAction.makeAction(state=state, entities=entities, args=args)

    result = action.applyInitiate()
    assert team.resources[entities.work] == 50

    result = action.revertInitiate()
    assert team.resources[entities.work] == 100

    args.vyroba = entities.vyrobas["vyr-drevo1Pro"]
    action = VyrobaAction.makeAction(state=state, entities=entities, args=args)

    result = action.applyInitiate()
    assert team.resources[entities.work] == 50
    assert team.resources[entities.obyvatel] == 90

    result = action.revertInitiate()
    assert team.resources[entities.obyvatel] == 100

    assert team.resources == originalResources


def test_simple():
    entities = TEST_ENTITIES
    state = createTestInitState()
    team = state.teamStates[teamEntity]
    team.resources[entities.resources["pro-drevo"]] = Decimal(20)
    originalResources = team.resources.copy()

    args = VyrobaArgs(
        vyroba=entities.vyrobas["vyr-drevo1Mat"],
        count=1,
        tile=team.homeTile.entity,
        team=teamEntity,
    )
    action = VyrobaAction.makeAction(state=state, entities=entities, args=args)

    initResult = action.applyInitiate()
    commitResult = action.commitThrows(throws=1, dots=5)

    assert team.resources == {
        entities.work: 80,
        entities.obyvatel: 100,
        entities.resources["pro-drevo"]: 20,
    }
    assert "Vydejte týmu" in commitResult.message
    assert "Tým obdržel" in commitResult.message


def test_production():
    entities = TEST_ENTITIES
    state = createTestInitState()
    team = state.teamStates[teamEntity]
    team.resources[entities.resources["pro-drevo"]] = Decimal(20)

    args = VyrobaArgs(
        vyroba=entities.vyrobas["vyr-drevo1Pro"],
        count=1,
        tile=team.homeTile.entity,
        team=teamEntity,
    )
    action = VyrobaAction.makeAction(state=state, entities=entities, args=args)

    initResult = action.applyInitiate()
    commitResult = action.commitThrows(throws=1, dots=5)

    assert team.resources == {
        entities.work: 80,
        entities.obyvatel: 98,
        entities.resources["pro-drevo"]: 21,
    }
    assert "Vydejte týmu" not in commitResult.message
    assert "Tým obdržel" in commitResult.message


def test_distance():
    entities = TEST_ENTITIES
    state = createTestInitState()
    team = state.teamStates[teamEntity]
    team.resources[entities.resources["pro-drevo"]] = Decimal(20)

    args = VyrobaArgs(
        vyroba=entities.vyrobas["vyr-drevo1Mat"],
        count=1,
        tile=entities.tiles["map-tile06"],
        team=teamEntity,
    )
    action = VyrobaAction.makeAction(state=state, entities=entities, args=args)
    commitResult = action.commitSuccess()
    assert len(commitResult.scheduledActions) == 1
    distance = commitResult.scheduledActions[0].delay_s
    assert distance == 600


def test_richnessMaterial():
    entities = TEST_ENTITIES
    state = createTestInitState()
    team = state.teamStates[entities.teams["tym-zluti"]]
    team.resources[entities.resources["pro-drevo"]] = Decimal(20)
    tile = state.map.tiles[27]
    sendArmyTo(entities, state, state.map.armies[3], tile.entity, equipment=8)

    args = VyrobaArgs(
        vyroba=entities.vyrobas["vyr-drevoLes"],
        count=2,
        tile=tile.entity,
        team=team.team,
    )
    action = VyrobaAction.makeAction(state=state, entities=entities, args=args)

    initResult = action.applyInitiate()
    commitResult = action.commitThrows(throws=1, dots=20)
    assert len(commitResult.scheduledActions) == 1
    scheduled = commitResult.scheduledActions[0]
    delayedResult = scheduled.actionType.makeAction(
        state, entities, scheduled.args
    ).commit()

    assert team.resources == {
        entities.work: 70,
        entities.obyvatel: 100,
        entities.resources["pro-drevo"]: 20,
    }
    assert "+80%" in delayedResult.message
    assert "[[mat-drevo|3]]" in delayedResult.message
    assert tile.richnessTokens == 8


def test_richnessProduction():
    entities = TEST_ENTITIES
    state = createTestInitState()
    team = state.teamStates[entities.teams["tym-zluti"]]
    team.resources[entities.resources["pro-drevo"]] = Decimal(20)
    tile = state.map.tiles[27]
    sendArmyTo(entities, state, state.map.armies[3], tile.entity, equipment=8)

    args = VyrobaArgs(
        vyroba=entities.vyrobas["vyr-drevoProdLes"],
        count=2,
        tile=tile.entity,
        team=team.team,
    )
    action = VyrobaAction.makeAction(state=state, entities=entities, args=args)

    initResult = action.applyInitiate()
    commitResult = action.commitThrows(throws=1, dots=20)
    assert len(commitResult.scheduledActions) == 1
    scheduled = commitResult.scheduledActions[0]
    delayedResult = scheduled.actionType.makeAction(
        state, entities, scheduled.args
    ).commit()

    assert team.resources == {
        entities.work: 70,
        entities.obyvatel: 98,
        entities.resources["pro-drevo"]: Decimal("23.6"),
    }
    assert "+80%" in delayedResult.message
    assert "[[pro-drevo|3.6]]" in delayedResult.message
    assert tile.richnessTokens == 8


def test_featureMissing():
    entities = TEST_ENTITIES
    state = createTestInitState()
    team = state.teamStates[entities.teams["tym-zluti"]]
    tile = state.map.tiles[27]
    team.resources[entities.resources["pro-drevo"]] = Decimal(20)

    args = VyrobaArgs(
        vyroba=entities.vyrobas["vyr-drevoProdLes"],
        count=2,
        tile=tile.entity,
        team=team.team,
    )
    action = VyrobaAction.makeAction(state=state, entities=entities, args=args)

    initResult = action.applyInitiate()
    with pytest.raises(ActionFailed) as einfo:
        action.commitThrows(throws=1, dots=100)
