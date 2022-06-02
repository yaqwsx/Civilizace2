from typing import Set
from game.actions.common import ActionException, ActionCost
from game.actions.redirectToGranary import ActionRedirect, ActionRedirectArgs
from game.actions.researchFinish import ActionResearchFinish
from game.actions.researchStart import ActionResearchStart, ActionResearchArgs
from game.entities import DieId
from game.tests.actions.common import TEAM_BASIC, TEST_ENTITIES, TEAM_ADVANCED, createTestInitState

import pytest

teamId = TEAM_BASIC

def test_empty():
    entities = TEST_ENTITIES
    state = createTestInitState()
    team = state.teamStates[teamId]
    productions = {}

    assert team.granary == {}, "Granary is not empty in initial state"

    action = ActionRedirect(
        state=state, entities=entities, args=ActionRedirectArgs(team=teamId, productions=productions))

    cost = action.cost()
    assert cost.resources == {}
    assert cost.allowedDice == set()
    assert cost.requiredDots == 0

    action.commit()

    assert team.granary == {}, "Granary is not empty after adding an empty set of productions"


def test_successBulk():
    entities = TEST_ENTITIES
    state = createTestInitState()
    team = state.teamStates[teamId]
    productions = {entities["pro-maso"]: 2, entities["pro-dobytek"]:1, entities["pro-bobule"]: 5}
    team.resources = productions.copy()

    action = ActionRedirect(
        state=state, entities=entities, args=ActionRedirectArgs(team=teamId, productions=productions))

    cost = action.cost()
    assert cost.resources == productions
    assert cost.allowedDice == set()
    assert cost.requiredDots == 0

    action.commit()

    assert team.granary == productions, "Granary does not contain expected productions"
    assert sum(team.resources.values()) == 0, "Team resources should have been emptied"



def test_failInsufficient():
    entities = TEST_ENTITIES
    state = createTestInitState()
    team = state.teamStates[teamId]
    productions = {entities["pro-maso"]: 2, entities["pro-dobytek"]:1, entities["pro-bobule"]: 5}
    team.resources = productions.copy()
    productions[entities["pro-dobytek"]] = 3

    action = ActionRedirect(
        state=state, entities=entities, args=ActionRedirectArgs(team=teamId, productions=productions))

    with pytest.raises(ActionException) as einfo:
        action.commit()


def test_failWrong():
    entities = TEST_ENTITIES
    state = createTestInitState()
    team = state.teamStates[teamId]
    productions = {entities["pro-maso"]: 2, entities["mat-dobytek"]:1, entities["pro-bobule"]: 5}
    team.resources = productions.copy()

    action = ActionRedirect(
        state=state, entities=entities, args=ActionRedirectArgs(team=teamId, productions=productions))

    with pytest.raises(ActionException) as einfo:
        action.commit()
