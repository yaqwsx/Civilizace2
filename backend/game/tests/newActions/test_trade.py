from typing import Set
from game.actionsNew.actionBaseNew import ActionFailed
from game.actionsNew.trade import ActionTrade, ActionTradeArgs
from game.tests.actions.common import TEAM_BASIC, TEST_ENTITIES, TEAM_ADVANCED, createTestInitState

import pytest

teamId = TEAM_BASIC

def test_cost():
    entities = TEST_ENTITIES
    state = createTestInitState()
    
    team = state.teamStates[teamId]
    team.resources[entities["pro-bobule"]] = 3
    team.resources[entities["pro-cukr"]] = 2
    team.resources[entities["pro-drevo"]] = 5

    cost = ActionTrade(state=state, entities=entities, args=ActionTradeArgs(team=teamId, receiver=TEAM_ADVANCED, production=entities["pro-bobule"], amount=2)).cost()
    assert cost == {entities["mge-obchod-2"]:2}

    cost = ActionTrade(state=state, entities=entities, args=ActionTradeArgs(team=teamId, receiver=TEAM_ADVANCED, production=entities["pro-cukr"], amount=1)).cost()
    assert cost == {entities["mge-obchod-6"]:1}

    cost = ActionTrade(state=state, entities=entities, args=ActionTradeArgs(team=teamId, receiver=TEAM_ADVANCED, production=entities["pro-drevo"], amount=3)).cost()
    assert cost == {entities["mge-obchod-3"]:3}


def test_success():
    entities = TEST_ENTITIES
    state = createTestInitState()
    team = state.teamStates[teamId]
    them = state.teamStates[TEAM_ADVANCED]

    team.resources = {entities["pro-bobule"]:10, entities["pro-drevo"]:5}
    them.resources = {}

    result = ActionTrade(state=state, entities=entities, args=ActionTradeArgs(team=teamId, receiver=TEAM_ADVANCED, production=entities["pro-bobule"], amount=2)).applyCommit()

    assert team.resources == {entities["pro-bobule"]:8, entities["pro-drevo"]:5}
    assert them.resources == {entities["pro-bobule"]:2}
    assert len(result.notifications[TEAM_ADVANCED]) == 1

    result = ActionTrade(state=state, entities=entities, args=ActionTradeArgs(team=teamId, receiver=TEAM_ADVANCED, production=entities["pro-bobule"], amount=2)).applyCommit()

    assert team.resources == {entities["pro-bobule"]:6, entities["pro-drevo"]:5}
    assert them.resources == {entities["pro-bobule"]:4}
    assert len(result.notifications[TEAM_ADVANCED]) == 1


def test_invalidResource():
    entities = TEST_ENTITIES
    state = createTestInitState()
    team = state.teamStates[teamId]
    them = state.teamStates[TEAM_ADVANCED]

    team.resources = {entities["pro-bobule"]:10, entities["pro-drevo"]:5}

    with pytest.raises(ActionFailed) as einfo:
        result = ActionTrade(state=state, entities=entities, args=ActionTradeArgs(team=teamId, receiver=TEAM_ADVANCED, production=entities["mat-bobule"], amount=2)).applyCommit()


def test_insufficient():
    entities = TEST_ENTITIES
    state = createTestInitState()
    team = state.teamStates[teamId]
    them = state.teamStates[TEAM_ADVANCED]

    team.resources = {entities["pro-bobule"]:10, entities["pro-drevo"]:5}

    with pytest.raises(ActionFailed) as einfo:
        result = ActionTrade(state=state, entities=entities, args=ActionTradeArgs(team=teamId, receiver=TEAM_ADVANCED, production=entities["pro-bobule"], amount=20)).applyCommit()


def test_unknownResource():
    entities = TEST_ENTITIES
    state = createTestInitState()
    team = state.teamStates[teamId]
    them = state.teamStates[TEAM_ADVANCED]

    team.resources = {entities["pro-bobule"]:10, entities["pro-drevo"]:5}

    with pytest.raises(ActionFailed) as einfo:
        result = ActionTrade(state=state, entities=entities, args=ActionTradeArgs(team=teamId, receiver=TEAM_ADVANCED, production=entities["pro-kuze"], amount=2)).applyCommit()

