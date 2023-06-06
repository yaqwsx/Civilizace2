from decimal import Decimal

import pytest

from game.actions.common import ActionFailed
from game.actions.trade import TradeAction, TradeArgs
from game.tests.actions.common import (
    TEAM_ADVANCED,
    TEAM_BASIC,
    TEST_ENTITIES,
    createTestInitState,
)

basicTeamEntity = TEAM_BASIC
advancedTeamEntity = TEAM_ADVANCED


def test_cost():
    entities = TEST_ENTITIES
    state = createTestInitState()

    team = state.teamStates[basicTeamEntity]
    team.resources[entities.productions["pro-bobule"]] = Decimal(3)
    team.resources[entities.productions["pro-cukr"]] = Decimal(2)
    team.resources[entities.productions["pro-drevo"]] = Decimal(5)

    cost = TradeAction.makeAction(
        state=state,
        entities=entities,
        args=TradeArgs(
            team=basicTeamEntity,
            receiver=advancedTeamEntity,
            resources={entities.productions["pro-bobule"]: Decimal(2)},
        ),
    ).cost()
    assert cost == {entities.resources["mge-obchod-2"]: 2}

    cost = TradeAction.makeAction(
        state=state,
        entities=entities,
        args=TradeArgs(
            team=basicTeamEntity,
            receiver=advancedTeamEntity,
            resources={entities.productions["pro-cukr"]: Decimal(1)},
        ),
    ).cost()
    assert cost == {entities.resources["mge-obchod-6"]: 1}

    cost = TradeAction.makeAction(
        state=state,
        entities=entities,
        args=TradeArgs(
            team=basicTeamEntity,
            receiver=advancedTeamEntity,
            resources={entities.productions["pro-drevo"]: Decimal(3)},
        ),
    ).cost()
    assert cost == {entities.resources["mge-obchod-3"]: 3}

    cost = TradeAction.makeAction(
        state=state,
        entities=entities,
        args=TradeArgs(
            team=basicTeamEntity,
            receiver=advancedTeamEntity,
            resources={
                entities.productions["pro-drevo"]: Decimal(3),
                entities.productions["pro-maso"]: Decimal(2),
            },
        ),
    ).cost()
    assert cost == {entities.resources["mge-obchod-3"]: 5}

    cost = TradeAction.makeAction(
        state=state,
        entities=entities,
        args=TradeArgs(
            team=basicTeamEntity,
            receiver=advancedTeamEntity,
            resources={
                entities.productions["pro-drevo"]: Decimal(3),
                entities.productions["pro-cukr"]: Decimal(2),
            },
        ),
    ).cost()
    assert cost == {
        entities.resources["mge-obchod-3"]: 3,
        entities.resources["mge-obchod-6"]: 2,
    }


def test_success():
    entities = TEST_ENTITIES
    state = createTestInitState()
    team = state.teamStates[basicTeamEntity]
    other = state.teamStates[advancedTeamEntity]

    team.resources = {
        entities.productions["pro-bobule"]: Decimal(10),
        entities.productions["pro-drevo"]: Decimal(5),
    }
    other.resources = {}

    result = TradeAction.makeAction(
        state=state,
        entities=entities,
        args=TradeArgs(
            team=basicTeamEntity,
            receiver=advancedTeamEntity,
            resources={entities.productions["pro-bobule"]: Decimal(2)},
        ),
    ).commitThrows(throws=0, dots=0)

    assert team.resources == {
        entities.productions["pro-bobule"]: 8,
        entities.productions["pro-drevo"]: 5,
    }
    assert other.resources == {entities.productions["pro-bobule"]: 2}
    assert len(result.notifications[advancedTeamEntity]) == 1

    result = TradeAction.makeAction(
        state=state,
        entities=entities,
        args=TradeArgs(
            team=basicTeamEntity,
            receiver=advancedTeamEntity,
            resources={
                entities.productions["pro-bobule"]: Decimal(2),
                entities.productions["pro-drevo"]: Decimal(2),
            },
        ),
    ).commitThrows(throws=0, dots=0)

    assert team.resources == {
        entities.productions["pro-bobule"]: 6,
        entities.productions["pro-drevo"]: 3,
    }
    assert other.resources == {
        entities.productions["pro-bobule"]: 4,
        entities.productions["pro-drevo"]: 2,
    }
    assert len(result.notifications[advancedTeamEntity]) == 1


def test_invalidResource():
    entities = TEST_ENTITIES
    state = createTestInitState()
    team = state.teamStates[basicTeamEntity]
    other = state.teamStates[advancedTeamEntity]

    team.resources = {
        entities.productions["pro-bobule"]: Decimal(10),
        entities.productions["pro-drevo"]: Decimal(5),
    }

    with pytest.raises(ActionFailed) as einfo:
        result = TradeAction.makeAction(
            state=state,
            entities=entities,
            args=TradeArgs(
                team=basicTeamEntity,
                receiver=advancedTeamEntity,
                resources={entities.resources["mat-bobule"]: Decimal(2)},
            ),
        ).commitThrows(throws=0, dots=0)


def test_insufficient():
    entities = TEST_ENTITIES
    state = createTestInitState()
    team = state.teamStates[basicTeamEntity]
    other = state.teamStates[advancedTeamEntity]

    team.resources = {
        entities.productions["pro-bobule"]: Decimal(10),
        entities.productions["pro-drevo"]: Decimal(5),
    }

    with pytest.raises(ActionFailed) as einfo:
        result = TradeAction.makeAction(
            state=state,
            entities=entities,
            args=TradeArgs(
                team=basicTeamEntity,
                receiver=advancedTeamEntity,
                resources={entities.productions["pro-bobule"]: Decimal(20)},
            ),
        ).commitThrows(throws=0, dots=0)


def test_unknownResource():
    entities = TEST_ENTITIES
    state = createTestInitState()
    team = state.teamStates[basicTeamEntity]
    other = state.teamStates[advancedTeamEntity]

    team.resources = {
        entities.productions["pro-bobule"]: Decimal(10),
        entities.productions["pro-drevo"]: Decimal(5),
    }

    with pytest.raises(ActionFailed) as einfo:
        result = TradeAction.makeAction(
            state=state,
            entities=entities,
            args=TradeArgs(
                team=basicTeamEntity,
                receiver=advancedTeamEntity,
                resources={entities.productions["pro-kuze"]: Decimal(2)},
            ),
        ).commitThrows(throws=0, dots=0)
