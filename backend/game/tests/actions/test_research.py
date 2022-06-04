from typing import Set
from game.actionsNew.actionBaseNew import ActionFailed
from game.actionsNew.researchFinishNew import ActionResearchFinishNew
from game.actionsNew.researchStartNew import ActionResearchArgsNew, ActionResearchStartNew
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

    action = ActionResearchStartNew(
        state=state, entities=entities, args=ActionResearchArgsNew(tech=tech, team=team))

    cost = action.cost()
    dice = action.diceRequirements()
    assert cost == tech.cost
    assert dice == (set([DieId("die-lesy")]), 20)

    action.applyCommit(1, 100)

    assert state.teamStates[team].researching == {tech}


def test_startOwned():
    entities = TEST_ENTITIES
    state = createTestInitState()

    action = ActionResearchStartNew(
        state=state, entities=entities, args=ActionResearchArgsNew(tech=entities["tec-start"], team=team))

    with pytest.raises(ActionFailed) as einfo:
        action.cost()
    with pytest.raises(ActionFailed) as einfo:
        action.applyCommit()


def test_startInProgress():
    entities = TEST_ENTITIES
    state = createTestInitState()
    state.teamStates[team].researching.add(entities["tec-c"])

    action = ActionResearchStartNew(
        state=state, entities=entities, args=ActionResearchArgsNew(tech=entities["tec-c"], team=team))

    with pytest.raises(ActionFailed) as einfo:
        action.applyCommit(1, 100)


def test_finish():
    entities = TEST_ENTITIES
    state = createTestInitState()
    tech = entities["tec-c"]
    state.teamStates[team].researching.add(entities["tec-c"])

    args = ActionResearchArgsNew(tech=tech, team=team)
    action = ActionResearchFinishNew(state=state, entities=entities, args=args)

    assert action.cost() == {}

    action.applyCommit(1, 100)
    assert len(state.teamStates[team].researching) == 0
    assert len(state.teamStates[team].techs) == 2
    assert tech in state.teamStates[team].techs


def test_finishOwned():
    entities = TEST_ENTITIES
    state = createTestInitState()

    action = ActionResearchFinishNew(state=state, entities=entities,
                                  args=ActionResearchArgsNew(tech=entities["tec-start"], team=team))
    with pytest.raises(ActionFailed) as einfo:
        action.applyCommit(1, 100)


def test_finishUnknown():
    entities = TEST_ENTITIES
    state = createTestInitState()

    action = ActionResearchFinishNew(state=state, entities=entities,
                                  args=ActionResearchArgsNew(tech=entities["tec-a"], team=team))
    with pytest.raises(ActionFailed) as einfo:
        action.applyCommit(1, 100)


def test_compound():
    entities = TEST_ENTITIES
    state = createTestInitState()

    ActionResearchStartNew(state=state, entities=entities,
                        args=ActionResearchArgsNew(tech=entities["tec-a"], team=team)).applyCommit(1, 100)
    ActionResearchFinishNew(state=state, entities=entities,
                         args=ActionResearchArgsNew(tech=entities["tec-a"], team=team)).applyCommit(1, 100)
    ActionResearchStartNew(state=state, entities=entities,
                        args=ActionResearchArgsNew(tech=entities["tec-c"], team=team)).applyCommit(1, 100)
    ActionResearchFinishNew(state=state, entities=entities,
                         args=ActionResearchArgsNew(tech=entities["tec-c"], team=team)).applyCommit(1, 100)
    ActionResearchStartNew(state=state, entities=entities,
                        args=ActionResearchArgsNew(tech=entities["tec-d"], team=team)).applyCommit(1, 100)


    teamState = state.teamStates[team]

    expected = {entities["tec-start"], entities["tec-a"], entities["tec-c"]}
    diff = teamState.techs.symmetric_difference(expected)
    assert len(diff) == 0
    assert len(teamState.researching) == 1
    assert entities["tec-d"] in teamState.researching
