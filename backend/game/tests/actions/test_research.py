from typing import Set
from game.actions.common import ActionException, ActionCost
from game.actions.researchFinish import ActionResearchFinish
from game.actions.researchStart import ActionResearchStart, ActionResearchArgs
from game.entities import DieId
from game.tests.actions.common import TEAM_BASIC, TEST_ENTITIES, TEAM_ADVANCED, createTestInitState

import pytest

team = TEAM_BASIC


def test_initialState():
    entities = TEST_ENTITIES
    state = createTestInitState()

    assert len(state.teamStates[team].researching) == 0
    assert len(state.teamStates[team].techs) == 1
    assert entities["tec-start"] in state.teamStates[team].techs


def test_start():
    entities = TEST_ENTITIES
    state = createTestInitState()
    tech = entities["tec-a"]

    action = ActionResearchStart(
        state=state, entities=entities, args=ActionResearchArgs(tech=tech, team=team))

    cost = action.cost()
    assert cost.resources == tech.cost
    assert cost.allowedDice == set([DieId("die-lesy")])

    action.commit()

    assert state.teamStates[team].researching == {tech}


def test_startOwned():
    entities = TEST_ENTITIES
    state = createTestInitState()

    action = ActionResearchStart(
        state=state, entities=entities, args=ActionResearchArgs(tech=entities["tec-start"], team=team))

    with pytest.raises(ActionException) as einfo:
        action.cost()
    with pytest.raises(ActionException) as einfo:
        action.commit()


def test_startInProgress():
    entities = TEST_ENTITIES
    state = createTestInitState()
    state.teamStates[team].researching.add(entities["tec-c"])

    action = ActionResearchStart(
        state=state, entities=entities, args=ActionResearchArgs(tech=entities["tec-c"], team=team))

    with pytest.raises(ActionException) as einfo:
        action.commit()


def test_finish():
    entities = TEST_ENTITIES
    state = createTestInitState()
    tech = entities["tec-c"]
    state.teamStates[team].researching.add(entities["tec-c"])

    action = ActionResearchFinish(state=state, entities=entities,
                                  args=ActionResearchArgs(tech=tech, team=team))

    assert action.cost() == ActionCost()

    action.commit()
    assert len(state.teamStates[team].researching) == 0
    assert len(state.teamStates[team].techs) == 2
    assert tech in state.teamStates[team].techs


def test_finishOwned():
    entities = TEST_ENTITIES
    state = createTestInitState()

    action = ActionResearchFinish(state=state, entities=entities,
                                  args=ActionResearchArgs(tech=entities["tec-start"], team=team))
    with pytest.raises(ActionException) as einfo:
        action.commit()


def test_finishUnknown():
    entities = TEST_ENTITIES
    state = createTestInitState()

    action = ActionResearchFinish(state=state, entities=entities,
                                  args=ActionResearchArgs(tech=entities["tec-a"], team=team))
    with pytest.raises(ActionException) as einfo:
        action.commit()


def test_compound():
    entities = TEST_ENTITIES
    state = createTestInitState()

    ActionResearchStart(state=state, entities=entities,
                        args=ActionResearchArgs(tech=entities["tec-a"], team=team)).commit()
    ActionResearchFinish(state=state, entities=entities,
                         args=ActionResearchArgs(tech=entities["tec-a"], team=team)).commit()
    ActionResearchStart(state=state, entities=entities,
                        args=ActionResearchArgs(tech=entities["tec-c"], team=team)).commit()
    ActionResearchFinish(state=state, entities=entities,
                         args=ActionResearchArgs(tech=entities["tec-c"], team=team)).commit()
    ActionResearchStart(state=state, entities=entities,
                        args=ActionResearchArgs(tech=entities["tec-d"], team=team)).commit()


    teamState = state.teamStates[team]

    expected = {entities["tec-start"], entities["tec-a"], entities["tec-c"]}
    diff = teamState.techs.symmetric_difference(expected)
    assert len(diff) == 0
    assert len(teamState.researching) == 1
    assert entities["tec-d"] in teamState.researching
