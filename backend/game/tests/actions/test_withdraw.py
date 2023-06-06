from decimal import Decimal

import pytest

from game.actions.common import ActionFailed
from game.actions.withdraw import WithdrawAction, WithdrawArgs
from game.tests.actions.common import TEAM_BASIC, TEST_ENTITIES, createTestInitState

entities = TEST_ENTITIES
teamEntity = TEAM_BASIC
sampleStorage = {
    entities.resources["mat-drevo"]: Decimal(10),
    entities.resources["mat-bobule"]: Decimal(5),
}


def test_withdraw():
    state = createTestInitState()
    teamState = state.teamStates[teamEntity]
    teamState.storage = sampleStorage.copy()

    args = WithdrawArgs(resources={entities.resources["mat-drevo"]: 2}, team=teamEntity)
    action = WithdrawAction.makeAction(state=state, entities=entities, args=args)

    result = action.commitThrows(throws=0, dots=0)
    assert teamState.storage[entities.resources["mat-drevo"]] == 8
    assert teamState.resources[entities.work] == 98

    result = action.commitThrows(throws=0, dots=0)
    assert teamState.storage[entities.resources["mat-drevo"]] == 6

    args.resources[entities.resources["mat-drevo"]] = 3
    args.resources[entities.resources["mat-bobule"]] = 5
    result = action.commitThrows(throws=0, dots=0)
    assert teamState.storage == {
        entities.resources["mat-drevo"]: 3,
        entities.resources["mat-bobule"]: 0,
    }
    assert "bobule" in result.message
    assert "drevo" in result.message
    assert teamState.resources[entities.work] == 88

    with pytest.raises(ActionFailed) as einfo:
        action.commitThrows(throws=0, dots=0)


def test_noWork():
    state = createTestInitState()
    teamState = state.teamStates[teamEntity]
    teamState.storage = sampleStorage.copy()
    teamState.resources[entities.work] = Decimal(1)

    args = WithdrawArgs(resources={entities.resources["mat-drevo"]: 2}, team=teamEntity)
    action = WithdrawAction.makeAction(state=state, entities=entities, args=args)

    with pytest.raises(ActionFailed) as einfo:
        action.commitThrows(throws=0, dots=0)
