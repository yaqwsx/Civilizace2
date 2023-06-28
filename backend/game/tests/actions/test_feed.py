from decimal import Decimal

import pytest

from game.actions.common import ActionFailed
from game.actions.feed import FeedAction, FeedArgs
from game.tests.actions.common import TEAM_BASIC, TEST_ENTITIES, createTestInitState

teamEntity = TEAM_BASIC

FOOD_ID = "mge-jidlo"


def test_simpleFeed():
    entities = TEST_ENTITIES
    state = createTestInitState()
    state.world.turn = 1

    assert state.teamStates[teamEntity].resources[entities.work] == 100
    assert state.teamStates[teamEntity].resources[entities.obyvatel] == 100

    action = FeedAction.makeAction(
        state=state,
        entities=entities,
        args=FeedArgs(team=teamEntity),
    )

    action.commitThrows(throws=0, dots=0)

    assert state.teamStates[teamEntity].population == 112
    assert state.teamStates[teamEntity].resources[entities.work] == 162
    assert state.teamStates[teamEntity].resources[entities.obyvatel] == 112


def test_starve():
    entities = TEST_ENTITIES
    state = createTestInitState()
    state.world.turn = 1

    assert state.teamStates[teamEntity].resources[entities.work] == 100
    assert state.teamStates[teamEntity].resources[entities.obyvatel] == 100

    state.teamStates[teamEntity].resources[entities.resources[FOOD_ID]] = Decimal(1)
    action = FeedAction.makeAction(
        state=state,
        entities=entities,
        args=FeedArgs(team=teamEntity),
    )

    action.commitThrows(throws=0, dots=0)

    assert state.teamStates[teamEntity].population == 82
    assert state.teamStates[teamEntity].resources[entities.work] == 132
    assert state.teamStates[teamEntity].resources[entities.obyvatel] == 82


def test_highlevelFood():
    entities = TEST_ENTITIES
    state = createTestInitState()
    state.world.turn = 1
    teamState = state.teamStates[teamEntity]

    teamState.population = Decimal(100)
    teamState.resources[entities.obyvatel] = Decimal(80)
    assert state.teamStates[teamEntity].resources[entities.work] == 100
    assert state.teamStates[teamEntity].population == 100

    state.teamStates[teamEntity].resources[entities.resources[FOOD_ID]] = Decimal(1000)
    action = FeedAction.makeAction(
        state=state,
        entities=entities,
        args=FeedArgs(team=teamEntity),
    )

    action.commitThrows(throws=0, dots=0)

    assert state.teamStates[teamEntity].population == 123
    assert state.teamStates[teamEntity].resources[entities.work] == 153
    assert state.teamStates[teamEntity].resources[entities.obyvatel] == 103


def test_repeatedFeed():
    entities = TEST_ENTITIES
    state = createTestInitState()
    state.world.turn = 1

    assert state.teamStates[teamEntity].resources[entities.work] == 100
    assert state.teamStates[teamEntity].resources[entities.obyvatel] == 100

    state.teamStates[teamEntity].resources[entities.resources[FOOD_ID]] = Decimal(10)
    action = FeedAction.makeAction(
        state=state,
        entities=entities,
        args=FeedArgs(team=teamEntity),
    )
    action.commitThrows(throws=0, dots=0)

    action = FeedAction.makeAction(
        state=state,
        entities=entities,
        args=FeedArgs(team=teamEntity),
    )

    with pytest.raises(ActionFailed):
        action.commitThrows(throws=0, dots=0)


def test_productions():
    entities = TEST_ENTITIES
    state = createTestInitState()
    state.world.turn = 1

    state.teamStates[teamEntity].resources = {
        entities.resources["res-kultura"]: Decimal(20),
        entities.resources["res-prace"]: Decimal(200),
        entities.resources["res-obyvatel"]: Decimal(400),
        entities.resources["pro-bobule"]: Decimal(20),
        entities.resources["pro-kuze"]: Decimal(5),
        entities.resources["pro-drevo"]: Decimal(3),
        entities.resources["mat-bobule"]: Decimal(8),
        entities.resources["mat-drevo"]: Decimal(3),
        entities.resources["mat-cukr"]: Decimal(6),
        entities.resources[FOOD_ID]: Decimal(11),
    }

    action = FeedAction.makeAction(
        state=state,
        entities=entities,
        args=FeedArgs(team=teamEntity),
    )
    action.commitThrows(throws=0, dots=0)

    assert state.teamStates[teamEntity].resources == {
        entities.resources["res-kultura"]: 20,
        entities.resources["res-prace"]: 100 + 417,
        entities.resources["res-obyvatel"]: 410 + 20 + 7,
        entities.resources["pro-bobule"]: 20,
        entities.resources["pro-kuze"]: 5,
        entities.resources["pro-drevo"]: 3,
        entities.resources["mat-bobule"]: 10,
        entities.resources["mat-drevo"]: 6,
        entities.resources["mat-cukr"]: 6,
        entities.resources["mat-kuze"]: 5,
        entities.resources[FOOD_ID]: 1,
    }
