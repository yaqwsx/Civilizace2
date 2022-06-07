from typing import Set
from game.actions.actionBase import makeAction
from game.actions.common import ActionFailed
from game.actions.granary import ActionGranary, ActionGranaryArgs
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

    action = makeAction(ActionGranary,
        state=state, entities=entities, args=ActionGranaryArgs(team=teamId, productions=productions))

    cost = action.cost()
    assert cost == {}

    action.applyCommit()

    assert team.granary == {}, "Granary is not empty after adding an empty set of productions"


def test_successBulk():
    entities = TEST_ENTITIES
    state = createTestInitState()
    team = state.teamStates[teamId]
    productions = {entities["pro-maso"]: 2, entities["pro-dobytek"]:1, entities["pro-bobule"]: 5}
    team.resources = productions.copy()

    action = makeAction(ActionGranary,
        state=state, entities=entities, args=ActionGranaryArgs(team=teamId, productions=productions))

    cost = action.cost()
    assert cost == productions

    action.applyCommit()

    assert team.granary == productions, "Granary does not contain expected productions"
    assert sum(team.resources.values()) == 0, "Team resources should have been emptied"



def test_failInsufficient():
    entities = TEST_ENTITIES
    state = createTestInitState()
    team = state.teamStates[teamId]
    productions = {entities["pro-maso"]: 2, entities["pro-dobytek"]:1, entities["pro-bobule"]: 5}
    team.resources = productions.copy()
    productions[entities["pro-dobytek"]] = 3

    action = makeAction(ActionGranary,
        state=state, entities=entities, args=ActionGranaryArgs(team=teamId, productions=productions))

    with pytest.raises(ActionFailed) as einfo:
        action.applyCommit()



def test_failWrong():
    entities = TEST_ENTITIES
    state = createTestInitState()
    team = state.teamStates[teamId]
    productions = {entities["pro-maso"]: 2, entities["mat-dobytek"]:1, entities["pro-bobule"]: 5}
    team.resources = productions.copy()

    action = makeAction(ActionGranary,
        state=state, entities=entities, args=ActionGranaryArgs(team=teamId, productions=productions))

    with pytest.raises(ActionFailed) as einfo:
        action.applyCommit()

