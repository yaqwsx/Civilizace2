from decimal import Decimal

import pytest

from game.actions.common import ActionFailed
from game.actions.researchStart import ResearchArgs, ResearchStartAction
from game.tests.actions.common import TEAM_BASIC, TEST_ENTITIES, createTestInitState

teamEntity = TEAM_BASIC


def test_payResources():
    entities = TEST_ENTITIES
    state = createTestInitState()

    action = ResearchStartAction.makeAction(
        state=state,
        entities=entities,
        args=ResearchArgs(tech=entities.techs["tec-a"], team=teamEntity),
    )

    teamState = state.teamStates[teamEntity]
    teamState.resources = {
        entities.work: Decimal(100),
        entities.obyvatel: Decimal(100),
        entities.resources["pro-bobule"]: Decimal(10),
        entities.resources["pro-drevo"]: Decimal(10),
        entities.resources["pro-kuze"]: Decimal(1),
    }

    result = action._payResources({entities.work: 10})
    assert result == {}
    assert teamState.resources == {
        entities.work: 90,
        entities.obyvatel: 100,
        entities.resources["pro-bobule"]: 10,
        entities.resources["pro-drevo"]: 10,
        entities.resources["pro-kuze"]: 1,
    }
    assert teamState.population == 100

    result = action._payResources({entities.obyvatel: 10})
    assert result == {}
    assert teamState.resources == {
        entities.work: 90,
        entities.obyvatel: 90,
        entities.resources["pro-bobule"]: 10,
        entities.resources["pro-drevo"]: 10,
        entities.resources["pro-kuze"]: 1,
    }
    assert teamState.population == 100

    result = action._payResources(
        {entities.resources["pro-bobule"]: 2, entities.resources["pro-drevo"]: 2}
    )
    assert result == {}
    assert teamState.resources == {
        entities.work: 90,
        entities.obyvatel: 90,
        entities.resources["pro-bobule"]: 8,
        entities.resources["pro-drevo"]: 8,
        entities.resources["pro-kuze"]: 1,
    }
    assert teamState.population == 100
    assert teamState.resources.get(entities.obyvatel, Decimal(0)) == 90

    result = action._payResources(
        {
            entities.resources["mat-bobule"]: 2,
            entities.resources["mat-drevo"]: 2,
        }
    )
    assert result == {
        entities.resources["mat-bobule"]: 2,
        entities.resources["mat-drevo"]: 2,
    }
    assert teamState.resources == {
        entities.work: 90,
        entities.obyvatel: 90,
        entities.resources["pro-bobule"]: 8,
        entities.resources["pro-drevo"]: 8,
        entities.resources["pro-kuze"]: 1,
    }
    assert teamState.population == 100

    result = action._payResources(
        {
            entities.resources["mat-bobule"]: 2,
            entities.resources["pro-drevo"]: 2,
            entities.obyvatel: 5,
            entities.work: 20,
        }
    )
    assert result == {entities.resources["mat-bobule"]: 2}
    assert teamState.resources == {
        entities.work: 70,
        entities.obyvatel: 85,
        entities.resources["pro-bobule"]: 8,
        entities.resources["pro-drevo"]: 6,
        entities.resources["pro-kuze"]: 1,
    }
    assert teamState.population == 100
    assert teamState.resources.get(entities.obyvatel, Decimal(0)) == 85

    with pytest.raises(ActionFailed) as einfo:
        action._payResources({entities.resources["pro-bobule"]: 10})

    with pytest.raises(ActionFailed) as einfo:
        action._payResources({entities.resources["pro-keramika"]: 10})

    with pytest.raises(ActionFailed) as einfo:
        action._payResources({entities.work: 100})


def test_receiveResources():
    entities = TEST_ENTITIES
    state = createTestInitState()
    action = ResearchStartAction.makeAction(
        state=state,
        entities=entities,
        args=ResearchArgs(tech=entities.techs["tec-a"], team=teamEntity),
    )

    teamState = state.teamStates[teamEntity]

    teamState.resources = {}

    withdraw = action._receiveResources({})
    assert teamState.resources == {}
    assert withdraw == {}

    withdraw = action._receiveResources(
        {entities.resources["mat-kuze"]: 2}, instantWithdraw=True
    )
    assert teamState.resources == {}
    assert withdraw == {entities.resources["mat-kuze"]: 2}

    withdraw = action._receiveResources({entities.resources["mat-kuze"]: 2})
    assert teamState.resources == {entities.resources["mat-kuze"]: 2}
    assert withdraw == {}

    withdraw = action._receiveResources({entities.resources["pro-kuze"]: 3})
    assert teamState.resources == {
        entities.resources["pro-kuze"]: 3,
        entities.resources["mat-kuze"]: 2,
    }
    assert withdraw == {}

    withdraw = action._receiveResources(
        {entities.resources["pro-kuze"]: 10, entities.resources["mat-kuze"]: 10}
    )
    assert teamState.resources == {
        entities.resources["pro-kuze"]: 13,
        entities.resources["mat-kuze"]: 10,
    }
    assert withdraw == {}
