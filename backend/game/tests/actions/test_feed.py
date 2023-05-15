from decimal import Decimal
from game.actions.actionBase import makeAction
from game.actions.common import ActionFailed
from game.actions.feed import (
    FeedAction,
    FeedArgs,
    FeedRequirements,
    computeFeedRequirements,
)
from game.tests.actions.common import TEAM_BASIC, TEST_ENTITIES, createTestInitState

import pytest

teamState = TEAM_BASIC


def test_feedRequirements_initial():
    entities = TEST_ENTITIES
    state = createTestInitState()

    expected = FeedRequirements(
        tokensRequired=5, tokensPerCaste=1, casteCount=3, automated=[]
    )

    actual = computeFeedRequirements(state, entities, teamState)
    assert (
        expected == actual
    ), f"Feed requirements do not match expected values\n  exp={expected}\n  actual={actual}"


def test_feedRequirements_some():
    entities = TEST_ENTITIES
    state = createTestInitState()

    teamState = state.teamStates[teamState]

    teamState.resources[entities.obyvatel] = 201
    teamState.granary = {entities["pro-maso"]: 2, entities["pro-bobule"]: 1}

    expected = FeedRequirements(
        tokensRequired=8,
        tokensPerCaste=2,
        casteCount=3,
        automated=[(entities["mat-maso"], 2), (entities["mat-bobule"], 1)],
    )

    actual = computeFeedRequirements(state, entities, teamState)
    assert (
        expected == actual
    ), f"Feed requirements do not match expected values\n  exp={expected}\n  act={actual}"


def test_feedRequirements_order():
    entities = TEST_ENTITIES
    state = createTestInitState()

    teamState = state.teamStates[teamState]

    teamState.resources[entities.obyvatel] = 201
    teamState.granary = {
        entities["pro-maso"]: 1,
        entities["pro-bobule"]: 3,
        entities["pro-kuze"]: 2,
        entities["pro-keramika"]: 2,
        entities["pro-cukr"]: 1,
    }

    expected = FeedRequirements(
        tokensRequired=8,
        tokensPerCaste=2,
        casteCount=3,
        automated=[
            (entities["mat-bobule"], 3),
            (entities["mat-cukr"], 1),
            (entities["mat-maso"], 1),
            (entities["mat-keramika"], 2),
            (entities["mat-kuze"], 2),
        ],
    )

    actual = computeFeedRequirements(state, entities, teamState)
    assert (
        expected.automated == actual.automated
    ), f"Feed requirement order does not match expected value\n  exp={expected.automated}\n  act={actual.automated}"


def test_simpleFeed():
    entities = TEST_ENTITIES
    state = createTestInitState()
    state.world.turn = 1

    assert state.teamStates[teamState].resources[entities.work] == 100
    assert state.teamStates[teamState].resources[entities.obyvatel] == 100

    action = makeAction(
        FeedAction,
        state=state,
        entities=entities,
        args=FeedArgs(team=teamState, materials={entities["mat-bobule"]: 10}),
    )

    action.applyCommit()

    assert state.teamStates[teamState].population == 112
    assert state.teamStates[teamState].resources[entities.work] == 162
    assert state.teamStates[teamState].resources[entities.obyvatel] == 112


def test_starve():
    entities = TEST_ENTITIES
    state = createTestInitState()
    state.world.turn = 1

    assert state.teamStates[teamState].resources[entities.work] == 100
    assert state.teamStates[teamState].resources[entities.obyvatel] == 100

    action = makeAction(
        FeedAction,
        state=state,
        entities=entities,
        args=FeedArgs(team=teamState, materials={entities["mat-bobule"]: 1}),
    )

    action.applyCommit()

    assert state.teamStates[teamState].population == 82
    assert state.teamStates[teamState].resources[entities.work] == 132
    assert state.teamStates[teamState].resources[entities.obyvatel] == 82


def test_highlevelFood():
    entities = TEST_ENTITIES
    state = createTestInitState()
    state.world.turn = 1

    state.teamStates[teamState].employees = 20
    state.teamStates[teamState].resources[entities.obyvatel] = Decimal(80)
    assert state.teamStates[teamState].resources[entities.work] == 100
    assert state.teamStates[teamState].population == 100

    action = makeAction(
        FeedAction,
        state=state,
        entities=entities,
        args=FeedArgs(
            team=teamState,
            materials={
                entities.resources["mat-bobule"]: 100,
                entities.resources["mat-cukr"]: 100,
                entities.resources["mat-maso"]: 100,
                entities.resources["mat-dobytek"]: 100,
            },
        ),
    )

    action.applyCommit()

    assert state.teamStates[teamState].population == 123
    assert state.teamStates[teamState].resources[entities.work] == 153
    assert state.teamStates[teamState].resources[entities.obyvatel] == 103


def test_highlevelLuxury():
    entities = TEST_ENTITIES
    state = createTestInitState()
    state.world.turn = 10

    state.teamStates[teamState].resources = {}
    state.teamStates[teamState].storage = {}
    state.teamStates[teamState].granary = {}
    state.teamStates[teamState].resources[entities.work] = Decimal(200)
    state.teamStates[teamState].resources[entities.obyvatel] = Decimal(400)
    state.teamStates[teamState].resources[entities.resources["res-kultura"]] = Decimal(
        50
    )
    state.teamStates[teamState].employees = 600

    action = makeAction(
        FeedAction,
        state=state,
        entities=entities,
        args=FeedArgs(
            team=teamState,
            materials={
                entities.resources["mat-bobule"]: 100,
                entities.resources["mat-cukr"]: 100,
                entities.resources["mat-maso"]: 100,
                entities.resources["mat-dobytek"]: 100,
                entities.resources["mat-kuze"]: 100,
                entities.resources["mat-keramika"]: 100,
                entities.resources["mat-sklo"]: 100,
                entities.resources["mat-bylina"]: 100,
            },
        ),
    )

    action.applyCommit()

    assert state.teamStates[teamState].population == 1038 + 50
    assert state.teamStates[teamState].resources[entities.work] == 538
    assert state.teamStates[teamState].resources[entities.obyvatel] == 488
    assert state.teamStates[teamState].storage == {}
    assert state.teamStates[teamState].granary == {}


def test_repeatedFeed():
    entities = TEST_ENTITIES
    state = createTestInitState()
    state.world.turn = 1

    assert state.teamStates[teamState].resources[entities.work] == 100
    assert state.teamStates[teamState].resources[entities.obyvatel] == 100

    action = makeAction(
        FeedAction,
        state=state,
        entities=entities,
        args=FeedArgs(team=teamState, materials={entities.resources["mat-bobule"]: 10}),
    )
    action.applyCommit()

    action = makeAction(
        FeedAction,
        state=state,
        entities=entities,
        args=FeedArgs(team=teamState, materials={entities.resources["mat-bobule"]: 10}),
    )

    with pytest.raises(ActionFailed) as einfo:
        action.applyCommit()


def test_productions():
    entities = TEST_ENTITIES
    state = createTestInitState()
    state.world.turn = 1

    state.teamStates[teamState].resources = {
        entities.resources["res-kultura"]: 20,
        entities.resources["res-prace"]: 200,
        entities.resources["res-obyvatel"]: 400,
        entities.resources["pro-bobule"]: 20,
        entities.resources["pro-kuze"]: 5,
        entities.resources["pro-drevo"]: 3,
    }
    state.teamStates[teamState].storage = {
        entities.resources["mat-bobule"]: 8,
        entities.resources["mat-drevo"]: 3,
        entities.resources["mat-cukr"]: 6,
    }
    state.teamStates[teamState].granary = {
        entities.resources["pro-bobule"]: 20,
        entities.resources["pro-kuze"]: 10,
        entities.resources["pro-maso"]: 8,
    }

    action = makeAction(
        FeedAction,
        state=state,
        entities=entities,
        args=FeedArgs(team=teamState, materials={entities.resources["mat-maso"]: 1}),
    )
    action.applyCommit()

    assert state.teamStates[teamState].resources == {
        entities.resources["res-kultura"]: 20,
        entities.resources["res-prace"]: 100 + 417,
        entities.resources["res-obyvatel"]: 410 + 20 + 7,
        entities.resources["pro-bobule"]: 20,
        entities.resources["pro-kuze"]: 5,
        entities.resources["pro-drevo"]: 3,
    }

    assert state.teamStates[teamState].storage == {
        entities.resources["mat-bobule"]: 10,
        entities.resources["mat-drevo"]: 6,
        entities.resources["mat-cukr"]: 6,
        entities.resources["mat-kuze"]: 5,
    }
    assert state.teamStates[teamState].granary == {
        entities.resources["pro-bobule"]: 20,
        entities.resources["pro-kuze"]: 10,
        entities.resources["pro-maso"]: 8,
    }
