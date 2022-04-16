from game.actions.common import ActionArgumentException, ActionCost
from game.actions.nextTurn import ActionNextTurn, ActionNextTurnArgs
from game.actions.researchFinish import ActionResearchFinish
from game.actions.researchStart import ActionResearchStart, ActionResearchArgs
from game.entities import Entities
from game.state import GameState
from game.tests.actions.common import TEST_ENTITIES, TEST_TEAM, createTestInitState

import pytest

team = TEST_TEAM


def test_initialState():
    entities = TEST_ENTITIES
    state = createTestInitState()

    assert len(state.teamStates[team].researching) == 1
    assert len(state.teamStates[team].techs) == 1
    assert entities["tec-start"] in state.teamStates[team].techs


def test_start():
    entities = TEST_ENTITIES
    state = createTestInitState()
    tech = entities["tec-a"]

    action = ActionResearchStart(
        state=state, entities=entities, teamEntity=team, args=ActionResearchArgs(tech=tech))

    cost = action.cost()
    assert len(cost.resources) == 0
    assert len(cost.allowedDice) == 1

    action.commit()

    researching = state.teamStates[team].researching
    assert len(researching) == 2
    assert tech in researching


def test_startOwned():
    entities = TEST_ENTITIES
    state = createTestInitState()

    action = ActionResearchStart(
        state=state, entities=entities, teamEntity=team, args=ActionResearchArgs(tech=entities["tec-start"]))

    with pytest.raises(ActionArgumentException) as einfo:
        action.cost()
    with pytest.raises(ActionArgumentException) as einfo:
        action.commit()


def test_startInProgress():
    entities = TEST_ENTITIES
    state = createTestInitState()

    action = ActionResearchStart(
        state=state, entities=entities, teamEntity=team, args=ActionResearchArgs(tech=entities["tec-c"]))

    with pytest.raises(ActionArgumentException) as einfo:
        action.cost()
    with pytest.raises(ActionArgumentException) as einfo:
        action.commit()


def test_finish():
    entities = TEST_ENTITIES
    state = createTestInitState()
    tech = entities["tec-c"]

    action = ActionResearchFinish(state=state, entities=entities,
                                  teamEntity=team, args=ActionResearchArgs(tech=tech))

    assert action.cost() == ActionCost()

    action.commit()
    assert len(state.teamStates[team].researching) == 0
    assert len(state.teamStates[team].techs) == 2
    assert tech in state.teamStates[team].techs


def test_finishOwned():
    entities = TEST_ENTITIES
    state = createTestInitState()

    action = ActionResearchFinish(state=state, entities=entities,
                                  teamEntity=team, args=ActionResearchArgs(tech=entities["tec-start"]))
    with pytest.raises(ActionArgumentException) as einfo:
        action.commit()


def test_finishUnknown():
    entities = TEST_ENTITIES
    state = createTestInitState()

    action = ActionResearchFinish(state=state, entities=entities,
                                  teamEntity=team, args=ActionResearchArgs(tech=entities["tec-a"]))
    with pytest.raises(ActionArgumentException) as einfo:
        action.commit()


def test_compound():
    entities = TEST_ENTITIES
    state = createTestInitState()

    ActionResearchStart(state=state, entities=entities, teamEntity=team,
                        args=ActionResearchArgs(tech=entities["tec-a"])).commit()
    ActionResearchFinish(state=state, entities=entities, teamEntity=team,
                         args=ActionResearchArgs(tech=entities["tec-a"])).commit()
    ActionResearchFinish(state=state, entities=entities, teamEntity=team,
                         args=ActionResearchArgs(tech=entities["tec-c"])).commit()
    ActionResearchStart(state=state, entities=entities, teamEntity=team,
                        args=ActionResearchArgs(tech=entities["tec-d"])).commit()

    teamState = state.teamStates[team]

    expected = {entities["tec-start"], entities["tec-a"], entities["tec-c"]}
    diff = teamState.techs.symmetric_difference(expected)
    assert len(diff) == 0
    assert len(teamState.researching) == 1
    assert entities["tec-d"] in teamState.researching