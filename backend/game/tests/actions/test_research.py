from typing import Set
from game.actions.actionBase import makeAction
from game.actions.common import ActionFailed
from game.actions.researchFinish import ResearchFinishAction
from game.actions.researchStart import ResearchArgs, ResearchStartAction
from game.entities import Die
from game.tests.actions.common import TEAM_BASIC, TEST_ENTITIES, TEAM_ADVANCED, createTestInitState

import pytest

teamState = TEAM_BASIC


def test_initialState():
    entities = TEST_ENTITIES
    state = createTestInitState()

    assert len(state.teamStates[teamState].researching) == 0
    assert len(state.teamStates[teamState].techs) == 1
    assert entities["tec-start"] in state.teamStates[teamState].techs


def test_start():
    entities = TEST_ENTITIES
    state = createTestInitState()
    tech = entities["tec-a"]

    action = makeAction(ResearchStartAction,
        state=state, entities=entities, args=ResearchArgs(tech=tech, team=teamState))

    cost = action.cost()
    points = action.pointsCost()
    assert cost == tech.cost
    assert points == 20

    action.applyCommit(1, 100)

    assert state.teamStates[teamState].researching == {tech}


def test_startOwned():
    entities = TEST_ENTITIES
    state = createTestInitState()

    action = makeAction(ResearchStartAction,
        state=state, entities=entities, args=ResearchArgs(tech=entities["tec-start"], team=teamState))

    with pytest.raises(ActionFailed) as einfo:
        action.cost()
    with pytest.raises(ActionFailed) as einfo:
        action.applyCommit()


def test_startInProgress():
    entities = TEST_ENTITIES
    state = createTestInitState()
    state.teamStates[teamState].researching.add(entities["tec-c"])

    action = makeAction(ResearchStartAction,
        state=state, entities=entities, args=ResearchArgs(tech=entities["tec-c"], team=teamState))

    with pytest.raises(ActionFailed) as einfo:
        action.applyCommit(1, 100)


def test_finish():
    entities = TEST_ENTITIES
    state = createTestInitState()
    tech = entities["tec-c"]
    state.teamStates[teamState].researching.add(entities["tec-c"])

    args = ResearchArgs(tech=tech, team=teamState)
    action = makeAction(ResearchFinishAction, state=state, entities=entities, args=args)

    assert action.cost() == {}

    action.applyCommit(1, 100)
    assert len(state.teamStates[teamState].researching) == 0
    assert len(state.teamStates[teamState].techs) == 2
    assert tech in state.teamStates[teamState].techs


def test_finishOwned():
    entities = TEST_ENTITIES
    state = createTestInitState()

    action = makeAction(ResearchFinishAction, state=state, entities=entities,
                                  args=ResearchArgs(tech=entities["tec-start"], team=teamState))
    with pytest.raises(ActionFailed) as einfo:
        action.applyCommit(1, 100)


def test_finishUnknown():
    entities = TEST_ENTITIES
    state = createTestInitState()

    action = makeAction(ResearchFinishAction, state=state, entities=entities,
                                  args=ResearchArgs(tech=entities["tec-a"], team=teamState))
    with pytest.raises(ActionFailed) as einfo:
        action.applyCommit(1, 100)


def test_compound():
    entities = TEST_ENTITIES
    state = createTestInitState()

    makeAction(ResearchStartAction,state=state, entities=entities,
                        args=ResearchArgs(tech=entities["tec-a"], team=teamState)).applyCommit(1, 100)
    makeAction(ResearchFinishAction, state=state, entities=entities,
                         args=ResearchArgs(tech=entities["tec-a"], team=teamState)).applyCommit(1, 100)
    makeAction(ResearchStartAction,state=state, entities=entities,
                        args=ResearchArgs(tech=entities["tec-c"], team=teamState)).applyCommit(1, 100)
    makeAction(ResearchFinishAction, state=state, entities=entities,
                         args=ResearchArgs(tech=entities["tec-c"], team=teamState)).applyCommit(1, 100)
    makeAction(ResearchStartAction,state=state, entities=entities,
                        args=ResearchArgs(tech=entities["tec-d"], team=teamState)).applyCommit(1, 100)


    teamState = state.teamStates[teamState]

    expected = {entities["tec-start"], entities["tec-a"], entities["tec-c"]}
    diff = teamState.techs.symmetric_difference(expected)
    assert len(diff) == 0
    assert len(teamState.researching) == 1
    assert entities["tec-d"] in teamState.researching
