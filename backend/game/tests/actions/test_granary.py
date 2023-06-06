from decimal import Decimal

import pytest

from game.actions.common import ActionFailed
from game.actions.granary import GranaryAction, GranaryArgs
from game.tests.actions.common import TEAM_BASIC, TEST_ENTITIES, createTestInitState

teamId = TEAM_BASIC


def test_empty():
    entities = TEST_ENTITIES
    state = createTestInitState()
    team = state.teamStates[teamId]
    productions = {}

    assert team.granary == {}, "Granary is not empty in initial state"

    action = GranaryAction.makeAction(
        state=state,
        entities=entities,
        args=GranaryArgs(team=teamId, productions=productions),
    )

    cost = action.cost()
    assert cost == {}

    action.commitThrows(throws=0, dots=0)

    assert (
        team.granary == {}
    ), "Granary is not empty after adding an empty set of productions"


def test_successBulk():
    entities = TEST_ENTITIES
    state = createTestInitState()
    team = state.teamStates[teamId]
    productions = {
        entities.productions["pro-maso"]: 2,
        entities.productions["pro-dobytek"]: 1,
        entities.productions["pro-bobule"]: 5,
    }
    team.resources = {prod: Decimal(amount) for prod, amount in productions.items()}

    action = GranaryAction.makeAction(
        state=state,
        entities=entities,
        args=GranaryArgs(team=teamId, productions=productions),
    )

    cost = action.cost()
    assert cost == productions

    action.applyInitiate()
    action.commitThrows(throws=0, dots=0)

    assert team.granary == productions, "Granary does not contain expected productions"
    assert sum(team.resources.values()) == 0, "Team resources should have been emptied"


def test_failInsufficient():
    entities = TEST_ENTITIES
    state = createTestInitState()
    team = state.teamStates[teamId]
    productions = {
        entities.productions["pro-maso"]: 2,
        entities.productions["pro-dobytek"]: 1,
        entities.productions["pro-bobule"]: 5,
    }
    team.resources = {prod: Decimal(amount) for prod, amount in productions.items()}
    productions[entities.productions["pro-dobytek"]] = 3

    action = GranaryAction.makeAction(
        state=state,
        entities=entities,
        args=GranaryArgs(team=teamId, productions=productions),
    )

    with pytest.raises(ActionFailed) as einfo:
        action.applyInitiate()
        action.commitThrows(throws=0, dots=0)


def test_failWrong():
    entities = TEST_ENTITIES
    state = createTestInitState()
    team = state.teamStates[teamId]
    productions = {
        entities.productions["pro-maso"]: 2,
        entities.resources["mat-dobytek"]: 1,
        entities.productions["pro-bobule"]: 5,
    }
    team.resources = {prod: Decimal(amount) for prod, amount in productions.items()}

    action = GranaryAction.makeAction(
        state=state,
        entities=entities,
        args=GranaryArgs(team=teamId, productions=productions),
    )

    with pytest.raises(ActionFailed) as einfo:
        action.commitThrows(throws=0, dots=0)
