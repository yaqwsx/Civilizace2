import pytest
from game.actions.actionBase import makeAction
from game.actions.common import ActionFailed
from game.actions.researchStart import ActionResearchArgs, ActionResearchStart
from game.tests.actions.common import TEAM_BASIC, TEST_ENTITIES, createTestInitState

team = TEAM_BASIC

def test_payResources():
    entities = TEST_ENTITIES
    state = createTestInitState()

    action = makeAction(ActionResearchStart,
        state=state, entities=entities, args=ActionResearchArgs(tech=entities["tec-a"], team=team))

    teamState = state.teamStates[team]
    teamState.resources = {
        entities["res-prace"]: 100,
        entities["res-obyvatel"]: 100,
        entities["res-zamestnanec"]: 100,
        entities["pro-bobule"]: 10,
        entities["pro-drevo"]: 10,
        entities["pro-kuze"]: 1,
    }

    result = action.payResources({entities["res-prace"]: 10})
    assert result == {}
    assert teamState.resources == {
        entities["res-prace"]: 90,
        entities["res-obyvatel"]: 100,
        entities["res-zamestnanec"]: 100,
        entities["pro-bobule"]: 10,
        entities["pro-drevo"]: 10,
        entities["pro-kuze"]: 1,
    }

    result = action.payResources({entities["res-obyvatel"]: 10})
    assert result == {}
    assert teamState.resources == {
        entities["res-prace"]: 90,
        entities["res-obyvatel"]: 90,
        entities["res-zamestnanec"]: 110,
        entities["pro-bobule"]: 10,
        entities["pro-drevo"]: 10,
        entities["pro-kuze"]: 1,
    }

    result = action.payResources({entities["pro-bobule"]: 2, entities["pro-drevo"]: 2})
    assert result == {}
    assert teamState.resources == {
        entities["res-prace"]: 90,
        entities["res-obyvatel"]: 90,
        entities["res-zamestnanec"]: 110,
        entities["pro-bobule"]: 8,
        entities["pro-drevo"]: 8,
        entities["pro-kuze"]: 1,
    }

    result = action.payResources({entities["mat-bobule"]: 2, entities["mat-drevo"]: 2, })
    assert result == {entities["mat-bobule"]: 2, entities["mat-drevo"]: 2}
    assert teamState.resources == {
        entities["res-prace"]: 90,
        entities["res-obyvatel"]: 90,
        entities["res-zamestnanec"]: 110,
        entities["pro-bobule"]: 8,
        entities["pro-drevo"]: 8,
        entities["pro-kuze"]: 1,
    }

    result = action.payResources({entities["mat-bobule"]: 2, entities["pro-drevo"]: 2,
                                     entities["res-obyvatel"]:5, entities["res-prace"]:20,})
    assert result == {entities["mat-bobule"]: 2}
    assert teamState.resources == {
        entities["res-prace"]: 70,
        entities["res-obyvatel"]: 85,
        entities["res-zamestnanec"]: 115,
        entities["pro-bobule"]: 8,
        entities["pro-drevo"]: 6,
        entities["pro-kuze"]: 1,
    }

    with pytest.raises(ActionFailed) as einfo:
        action.payResources({entities["pro-bobule"]: 10})

    with pytest.raises(ActionFailed) as einfo:
        action.payResources({entities["pro-keramika"]: 10})

    with pytest.raises(ActionFailed) as einfo:
        action.payResources({entities["res-prace"]: 100})


def test_receiveResources():
    entities = TEST_ENTITIES
    state = createTestInitState()
    action = makeAction(ActionResearchStart,
        state=state, entities=entities, args=ActionResearchArgs(tech=entities["tec-a"], team=team))

    teamState = state.teamStates[team]

    teamState.storage = {}
    teamState.resources = {}

    withdraw = action.receiveResources({})
    assert teamState.resources == {}
    assert teamState.storage == {}
    assert withdraw == {}

    withdraw = action.receiveResources({entities["mat-kuze"]:2}, instantWithdraw=True)
    assert teamState.resources == {}
    assert teamState.storage == {}
    assert withdraw == {entities["mat-kuze"]:2}

    withdraw = action.receiveResources({entities["mat-kuze"]:2})
    assert teamState.resources == {}
    assert teamState.storage == {entities["mat-kuze"]:2}
    assert withdraw == {}

    withdraw = action.receiveResources({entities["pro-kuze"]:3})
    assert teamState.resources == {entities["pro-kuze"]:3}
    assert teamState.storage == {entities["mat-kuze"]:2}
    assert withdraw == {}

    withdraw = action.receiveResources({entities["pro-kuze"]:10, entities["mat-kuze"]: 10})
    assert teamState.resources == {entities["pro-kuze"]:13}
    assert teamState.storage == {entities["mat-kuze"]:10}
    assert withdraw == {}
