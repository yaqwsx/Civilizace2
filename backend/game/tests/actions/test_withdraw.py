from game.actions.actionBase import makeAction
from game.actions.common import ActionFailed
from game.actions.withdraw import WithdrawAction, WithdrawArgs
from game.tests.actions.common import TEAM_BASIC, TEST_ENTITIES, createTestInitState

import pytest

entities = TEST_ENTITIES
teamState = TEAM_BASIC
sampleStorage = {entities["mat-drevo"]:10, entities["mat-bobule"]:5}

def test_withdraw():
    state = createTestInitState()
    teamState = state.teamStates[teamState]
    teamState.storage = sampleStorage.copy()

    args = WithdrawArgs(resources = {entities["mat-drevo"]:2}, team=teamState)
    action = makeAction(WithdrawAction, state=state, entities=entities, args=args)

    result = action.applyCommit()
    assert teamState.storage[entities["mat-drevo"]] == 8
    assert teamState.resources[entities.work] == 98

    result = action.applyCommit()
    assert teamState.storage[entities["mat-drevo"]] == 6

    args.resources[entities["mat-drevo"]] = 3
    args.resources[entities["mat-bobule"]] = 5
    result = action.applyCommit()
    assert teamState.storage == {entities["mat-drevo"]:3, entities["mat-bobule"]:0}
    assert "bobule" in result.message
    assert "drevo" in result.message
    assert teamState.resources[entities.work] == 88

    with pytest.raises(ActionFailed) as einfo:
        action.applyCommit()


def test_noWork():
    state = createTestInitState()
    teamState = state.teamStates[teamState]
    teamState.storage = sampleStorage.copy()
    teamState.resources[entities.work] = 1

    args = WithdrawArgs(resources = {entities["mat-drevo"]:2}, team=teamState)
    action = makeAction(WithdrawAction, state=state, entities=entities, args=args)

    with pytest.raises(ActionFailed) as einfo:
        action.applyCommit()
