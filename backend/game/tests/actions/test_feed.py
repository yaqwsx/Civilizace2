from game.actions.feed import FeedRequirements, computeFeedRequirements
from game.tests.actions.common import TEAM_BASIC, TEST_ENTITIES, TEAM_ADVANCED, createTestInitState

import pytest

team = TEAM_BASIC


def test_feedRequirements_initial():
    entities = TEST_ENTITIES
    state = createTestInitState()

    expected = FeedRequirements(
        tokensRequired=5,
        tokensPerCaste=2,
        casteCount=3,
        automated={}
    )

    actual = computeFeedRequirements(state, entities, team)
    assert expected == actual, f"Feed requirements do not match expected values\n  exp={expected}\n  actual={actual}"


def test_feedRequirements_some():
    entities = TEST_ENTITIES
    state = createTestInitState()

    teamState = state.teamStates[team]

    teamState.granary = {entities["pro-maso"]:2, entities["pro-bobule"]: 1}

    expected = FeedRequirements(
        tokensRequired=2,
        tokensPerCaste=2,
        casteCount=3,
        automated=[(entities["mat-maso"], 2), (entities["mat-bobule"],1)]
    )

    actual = computeFeedRequirements(state, entities, team)
    assert expected == actual, f"Feed requirements do not match expected values\n  exp={expected}\n  actual={actual}"


