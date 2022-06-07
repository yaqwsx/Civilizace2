from game.actions.common import ActionException, ActionFailed
from game.actions.feed import ActionFeed, ActionFeedArgs, FeedRequirements, computeFeedRequirements
from game.tests.actions.common import TEAM_BASIC, TEST_ENTITIES, TEAM_ADVANCED, createTestInitState

import pytest

team = TEAM_BASIC


def test_feedRequirements_initial():
    entities = TEST_ENTITIES
    state = createTestInitState()

    expected = FeedRequirements(
        tokensRequired=5,
        tokensPerCaste=1,
        casteCount=3,
        automated=[]
    )

    actual = computeFeedRequirements(state, entities, team)
    assert expected == actual, f"Feed requirements do not match expected values\n  exp={expected}\n  actual={actual}"


def test_feedRequirements_some():
    entities = TEST_ENTITIES
    state = createTestInitState()

    teamState = state.teamStates[team]

    teamState.resources[entities.obyvatel] = 201
    teamState.granary = {entities["pro-maso"]: 2, entities["pro-bobule"]: 1}

    expected = FeedRequirements(
        tokensRequired=8,
        tokensPerCaste=2,
        casteCount=3,
        automated=[(entities["mat-maso"], 2), (entities["mat-bobule"], 1)]
    )

    actual = computeFeedRequirements(state, entities, team)
    assert expected == actual, f"Feed requirements do not match expected values\n  exp={expected}\n  act={actual}"


def test_feedRequirements_order():
    entities = TEST_ENTITIES
    state = createTestInitState()

    teamState = state.teamStates[team]

    teamState.resources[entities.obyvatel] = 201
    teamState.granary = {entities["pro-maso"]: 1, entities["pro-bobule"]: 3,
                         entities["pro-kuze"]: 2, entities["pro-keramika"]: 2, entities["pro-cukr"]: 1}

    expected = FeedRequirements(
        tokensRequired=8,
        tokensPerCaste=2,
        casteCount=3,
        automated=[(entities["mat-bobule"], 3), (entities["mat-cukr"], 1),
                   (entities["mat-maso"], 1), (entities["mat-keramika"], 2), (entities["mat-kuze"], 2)]
    )

    actual = computeFeedRequirements(state, entities, team)
    assert expected.automated == actual.automated, f"Feed requirement order does not match expected value\n  exp={expected.automated}\n  act={actual.automated}"


def test_simpleFeed():
    entities = TEST_ENTITIES
    state = createTestInitState()
    state.turn = 1

    assert state.teamStates[team].resources[entities.work] == 100
    assert state.teamStates[team].resources[entities.obyvatel] == 100

    action = ActionFeed(state=state, entities=entities, args=ActionFeedArgs(
        team=team, materials={entities["mat-bobule"]: 10}))

    action.applyCommit()

    assert state.teamStates[team].population == 112
    assert state.teamStates[team].resources[entities.work] == 162
    assert state.teamStates[team].resources[entities.obyvatel] == 112


def test_starve():
    entities = TEST_ENTITIES
    state = createTestInitState()
    state.turn = 1

    assert state.teamStates[team].resources[entities.work] == 100
    assert state.teamStates[team].resources[entities.obyvatel] == 100

    action = ActionFeed(state=state, entities=entities, args=ActionFeedArgs(
        team=team, materials={entities["mat-bobule"]: 1}))

    action.applyCommit()

    assert state.teamStates[team].population == 82
    assert state.teamStates[team].resources[entities.work] == 132
    assert state.teamStates[team].resources[entities.obyvatel] == 82


def test_highlevelFood():
    entities = TEST_ENTITIES
    state = createTestInitState()
    state.turn = 1

    state.teamStates[team].resources[entities["res-zamestnanec"]] = 20
    state.teamStates[team].resources[entities.obyvatel] = 80
    assert state.teamStates[team].resources[entities.work] == 100
    assert state.teamStates[team].population == 100

    action = ActionFeed(state=state, entities=entities, args=ActionFeedArgs(team=team, materials={
        entities["mat-bobule"]: 100,
        entities["mat-cukr"]: 100,
        entities["mat-maso"]: 100,
        entities["mat-dobytek"]: 100
    }))

    action.applyCommit()

    assert state.teamStates[team].population == 123
    assert state.teamStates[team].resources[entities.work] == 153
    assert state.teamStates[team].resources[entities.obyvatel] == 103


def test_highlevelLuxury():
    entities = TEST_ENTITIES
    state = createTestInitState()
    state.turn = 10

    state.teamStates[team].resources = {}
    state.teamStates[team].storage = {}
    state.teamStates[team].granary = {}
    state.teamStates[team].resources[entities["res-zamestnanec"]] = 600
    state.teamStates[team].resources[entities.work] = 200
    state.teamStates[team].resources[entities.obyvatel] = 400
    state.teamStates[team].resources[entities["res-kultura"]] = 50

    action = ActionFeed(state=state, entities=entities, args=ActionFeedArgs(team=team, materials={
        entities["mat-bobule"]: 100,
        entities["mat-cukr"]: 100,
        entities["mat-maso"]: 100,
        entities["mat-dobytek"]: 100,
        entities["mat-kuze"]: 100,
        entities["mat-keramika"]: 100,
        entities["mat-sperk"]: 100,
        entities["mat-bylina"]: 100
    }))

    action.applyCommit()

    assert state.teamStates[team].population == 1038 + 50
    assert state.teamStates[team].resources[entities.work] == 538
    assert state.teamStates[team].resources[entities.obyvatel] == 488
    assert state.teamStates[team].storage == {}
    assert state.teamStates[team].granary == {}


def test_repeatedFeed():
    entities = TEST_ENTITIES
    state = createTestInitState()
    state.turn = 1

    assert state.teamStates[team].resources[entities.work] == 100
    assert state.teamStates[team].resources[entities.obyvatel] == 100

    action = ActionFeed(state=state, entities=entities, args=ActionFeedArgs(
        team=team, materials={entities["mat-bobule"]: 10}))
    action.applyCommit()

    action = ActionFeed(state=state, entities=entities, args=ActionFeedArgs(
        team=team, materials={entities["mat-bobule"]: 10}))

    with pytest.raises(ActionFailed) as einfo:
        action.applyCommit()


def test_productions():
    entities = TEST_ENTITIES
    state = createTestInitState()
    state.turn = 1

    state.teamStates[team].resources = {
        entities["res-zamestnanec"]: 100,
        entities["res-kultura"]: 20,
        entities["res-prace"]: 200,
        entities["res-obyvatel"]: 400,
        entities["pro-bobule"]: 20,
        entities["pro-kuze"]: 5,
        entities["pro-drevo"]: 3
    }
    state.teamStates[team].storage = {
        entities["mat-bobule"]: 8,
        entities["mat-drevo"]: 3,
        entities["mat-cukr"]: 6
    }
    state.teamStates[team].granary = {
        entities["pro-bobule"]: 20,
        entities["pro-kuze"]: 10,
        entities["pro-maso"]: 8
    }

    action = ActionFeed(state=state, entities=entities, args=ActionFeedArgs(
        team=team, materials={entities["mat-maso"]: 1}))
    action.applyCommit()

    assert state.teamStates[team].resources == {
        entities["res-zamestnanec"]: 100,
        entities["res-kultura"]: 20,
        entities["res-prace"]: 100 + 417,
        entities["res-obyvatel"]: 410 + 20 + 7,
        entities["pro-bobule"]: 20,
        entities["pro-kuze"]: 5,
        entities["pro-drevo"]: 3
    }

    assert state.teamStates[team].storage == {
        entities["mat-bobule"]: 10,
        entities["mat-drevo"]: 6,
        entities["mat-cukr"]: 6,
        entities["mat-kuze"]: 5
    }
    assert state.teamStates[team].granary == {
        entities["pro-bobule"]: 20,
        entities["pro-kuze"]: 10,
        entities["pro-maso"]: 8
    }
