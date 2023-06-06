from decimal import Decimal

import pytest

from game.actions.common import ActionFailed
from game.actions.feed import (
    FeedAction,
    FeedArgs,
    FeedRequirements,
    computeFeedRequirements,
)
from game.tests.actions.common import TEAM_BASIC, TEST_ENTITIES, createTestInitState

teamEntity = TEAM_BASIC


def test_feedRequirements_initial():
    entities = TEST_ENTITIES
    state = createTestInitState()

    expected = FeedRequirements(
        tokensRequired=5, tokensPerCaste=1, casteCount=3, automated=[]
    )

    actual = computeFeedRequirements(state, entities, teamEntity)
    assert (
        expected == actual
    ), f"Feed requirements do not match expected values\n  exp={expected}\n  actual={actual}"


def test_feedRequirements_some():
    entities = TEST_ENTITIES
    state = createTestInitState()

    teamState = state.teamStates[teamEntity]

    teamState.resources[entities.obyvatel] = Decimal(201)
    teamState.granary = {
        entities.productions["pro-maso"]: Decimal(2),
        entities.productions["pro-bobule"]: Decimal(1),
    }

    expected = FeedRequirements(
        tokensRequired=8,
        tokensPerCaste=2,
        casteCount=3,
        automated=[
            (entities.resources["mat-maso"], Decimal(2)),
            (entities.resources["mat-bobule"], Decimal(1)),
        ],
    )

    actual = computeFeedRequirements(state, entities, teamEntity)
    assert (
        expected == actual
    ), f"Feed requirements do not match expected values\n  exp={expected}\n  act={actual}"


def test_feedRequirements_order():
    entities = TEST_ENTITIES
    state = createTestInitState()

    teamState = state.teamStates[teamEntity]

    teamState.resources[entities.obyvatel] = Decimal(201)
    teamState.granary = {
        entities.productions["pro-maso"]: Decimal(1),
        entities.productions["pro-bobule"]: Decimal(3),
        entities.productions["pro-kuze"]: Decimal(2),
        entities.productions["pro-keramika"]: Decimal(2),
        entities.productions["pro-cukr"]: Decimal(1),
    }

    expected = FeedRequirements(
        tokensRequired=8,
        tokensPerCaste=2,
        casteCount=3,
        automated=[
            (entities.resources["mat-bobule"], Decimal(3)),
            (entities.resources["mat-cukr"], Decimal(1)),
            (entities.resources["mat-maso"], Decimal(1)),
            (entities.resources["mat-keramika"], Decimal(2)),
            (entities.resources["mat-kuze"], Decimal(2)),
        ],
    )

    actual = computeFeedRequirements(state, entities, teamEntity)
    assert (
        expected.automated == actual.automated
    ), f"Feed requirement order does not match expected value\n  exp={expected.automated}\n  act={actual.automated}"


def test_simpleFeed():
    entities = TEST_ENTITIES
    state = createTestInitState()
    state.world.turn = 1

    assert state.teamStates[teamEntity].resources[entities.work] == 100
    assert state.teamStates[teamEntity].resources[entities.obyvatel] == 100

    action = FeedAction.makeAction(
        state=state,
        entities=entities,
        args=FeedArgs(
            team=teamEntity, materials={entities.resources["mat-bobule"]: 10}
        ),
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

    action = FeedAction.makeAction(
        state=state,
        entities=entities,
        args=FeedArgs(team=teamEntity, materials={entities.resources["mat-bobule"]: 1}),
    )

    action.commitThrows(throws=0, dots=0)

    assert state.teamStates[teamEntity].population == 82
    assert state.teamStates[teamEntity].resources[entities.work] == 132
    assert state.teamStates[teamEntity].resources[entities.obyvatel] == 82


def test_highlevelFood():
    entities = TEST_ENTITIES
    state = createTestInitState()
    state.world.turn = 1

    state.teamStates[teamEntity].employees = Decimal(20)
    state.teamStates[teamEntity].resources[entities.obyvatel] = Decimal(80)
    assert state.teamStates[teamEntity].resources[entities.work] == 100
    assert state.teamStates[teamEntity].population == 100

    action = FeedAction.makeAction(
        state=state,
        entities=entities,
        args=FeedArgs(
            team=teamEntity,
            materials={
                entities.resources["mat-bobule"]: 100,
                entities.resources["mat-cukr"]: 100,
                entities.resources["mat-maso"]: 100,
                entities.resources["mat-dobytek"]: 100,
            },
        ),
    )

    action.commitThrows(throws=0, dots=0)

    assert state.teamStates[teamEntity].population == 123
    assert state.teamStates[teamEntity].resources[entities.work] == 153
    assert state.teamStates[teamEntity].resources[entities.obyvatel] == 103


def test_highlevelLuxury():
    entities = TEST_ENTITIES
    state = createTestInitState()
    state.world.turn = 10

    state.teamStates[teamEntity].resources = {}
    state.teamStates[teamEntity].storage = {}
    state.teamStates[teamEntity].granary = {}
    state.teamStates[teamEntity].resources[entities.work] = Decimal(200)
    state.teamStates[teamEntity].resources[entities.obyvatel] = Decimal(400)
    state.teamStates[teamEntity].resources[entities.resources["res-kultura"]] = Decimal(
        50
    )
    state.teamStates[teamEntity].employees = Decimal(600)

    action = FeedAction.makeAction(
        state=state,
        entities=entities,
        args=FeedArgs(
            team=teamEntity,
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

    action.commitThrows(throws=0, dots=0)

    assert state.teamStates[teamEntity].population == 1038 + 50
    assert state.teamStates[teamEntity].resources[entities.work] == 538
    assert state.teamStates[teamEntity].resources[entities.obyvatel] == 488
    assert state.teamStates[teamEntity].storage == {}
    assert state.teamStates[teamEntity].granary == {}


def test_repeatedFeed():
    entities = TEST_ENTITIES
    state = createTestInitState()
    state.world.turn = 1

    assert state.teamStates[teamEntity].resources[entities.work] == 100
    assert state.teamStates[teamEntity].resources[entities.obyvatel] == 100

    action = FeedAction.makeAction(
        state=state,
        entities=entities,
        args=FeedArgs(
            team=teamEntity, materials={entities.resources["mat-bobule"]: 10}
        ),
    )
    action.commitThrows(throws=0, dots=0)

    action = FeedAction.makeAction(
        state=state,
        entities=entities,
        args=FeedArgs(
            team=teamEntity, materials={entities.resources["mat-bobule"]: 10}
        ),
    )

    with pytest.raises(ActionFailed) as einfo:
        action.commitThrows(throws=0, dots=0)


def test_productions():
    entities = TEST_ENTITIES
    state = createTestInitState()
    state.world.turn = 1

    state.teamStates[teamEntity].resources = {
        entities.resources["res-kultura"]: Decimal(20),
        entities.resources["res-prace"]: Decimal(200),
        entities.resources["res-obyvatel"]: Decimal(400),
        entities.productions["pro-bobule"]: Decimal(20),
        entities.productions["pro-kuze"]: Decimal(5),
        entities.productions["pro-drevo"]: Decimal(3),
    }
    state.teamStates[teamEntity].storage = {
        entities.resources["mat-bobule"]: Decimal(8),
        entities.resources["mat-drevo"]: Decimal(3),
        entities.resources["mat-cukr"]: Decimal(6),
    }
    state.teamStates[teamEntity].granary = {
        entities.productions["pro-bobule"]: Decimal(20),
        entities.productions["pro-kuze"]: Decimal(10),
        entities.productions["pro-maso"]: Decimal(8),
    }

    action = FeedAction.makeAction(
        state=state,
        entities=entities,
        args=FeedArgs(team=teamEntity, materials={entities.resources["mat-maso"]: 1}),
    )
    action.commitThrows(throws=0, dots=0)

    assert state.teamStates[teamEntity].resources == {
        entities.resources["res-kultura"]: 20,
        entities.resources["res-prace"]: 100 + 417,
        entities.resources["res-obyvatel"]: 410 + 20 + 7,
        entities.productions["pro-bobule"]: 20,
        entities.productions["pro-kuze"]: 5,
        entities.productions["pro-drevo"]: 3,
    }

    assert state.teamStates[teamEntity].storage == {
        entities.resources["mat-bobule"]: 10,
        entities.resources["mat-drevo"]: 6,
        entities.resources["mat-cukr"]: 6,
        entities.resources["mat-kuze"]: 5,
    }
    assert state.teamStates[teamEntity].granary == {
        entities.productions["pro-bobule"]: 20,
        entities.productions["pro-kuze"]: 10,
        entities.productions["pro-maso"]: 8,
    }
