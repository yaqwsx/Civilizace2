from typing import Set
from game.actions.actionBase import makeAction
from game.actions.common import ActionFailed
from game.actions.researchFinish import ActionResearchFinish
from game.actions.researchStart import ActionResearchArgs, ActionResearchStart
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

    action = makeAction(ActionResearchStart,
        state=state, entities=entities, args=ActionResearchArgs(tech=tech, team=team))

    cost = action.cost()
    dice, points = action.diceRequirements()
    assert cost == tech.cost
    assert set(dice) == set(["die-lesy"])
    assert points == 20

    action.applyCommit(1, 100)

    assert state.teamStates[team].researching == {tech}


def test_startOwned():
    entities = TEST_ENTITIES
    state = createTestInitState()

    action = makeAction(ActionResearchStart,
        state=state, entities=entities, args=ActionResearchArgs(tech=entities["tec-start"], team=team))

    with pytest.raises(ActionFailed) as einfo:
        action.cost()
    with pytest.raises(ActionFailed) as einfo:
        action.applyCommit()


def test_startInProgress():
    entities = TEST_ENTITIES
    state = createTestInitState()
    state.teamStates[team].researching.add(entities["tec-c"])

    action = makeAction(ActionResearchStart,
        state=state, entities=entities, args=ActionResearchArgs(tech=entities["tec-c"], team=team))

    with pytest.raises(ActionFailed) as einfo:
        action.applyCommit(1, 100)


def test_finish():
    entities = TEST_ENTITIES
    state = createTestInitState()
    tech = entities["tec-c"]
    state.teamStates[team].researching.add(entities["tec-c"])

    args = ActionResearchArgs(tech=tech, team=team)
    action = makeAction(ActionResearchFinish, state=state, entities=entities, args=args)

    assert action.cost() == {}

    action.applyCommit(1, 100)
    assert len(state.teamStates[team].researching) == 0
    assert len(state.teamStates[team].techs) == 2
    assert tech in state.teamStates[team].techs


def test_finishOwned():
    entities = TEST_ENTITIES
    state = createTestInitState()

    action = makeAction(ActionResearchFinish, state=state, entities=entities,
                                  args=ActionResearchArgs(tech=entities["tec-start"], team=team))
    with pytest.raises(ActionFailed) as einfo:
        action.applyCommit(1, 100)


def test_finishUnknown():
    entities = TEST_ENTITIES
    state = createTestInitState()

    action = makeAction(ActionResearchFinish, state=state, entities=entities,
                                  args=ActionResearchArgs(tech=entities["tec-a"], team=team))
    with pytest.raises(ActionFailed) as einfo:
        action.applyCommit(1, 100)


def test_compound():
    entities = TEST_ENTITIES
    state = createTestInitState()

    makeAction(ActionResearchStart,state=state, entities=entities,
                        args=ActionResearchArgs(tech=entities["tec-a"], team=team)).applyCommit(1, 100)
    makeAction(ActionResearchFinish, state=state, entities=entities,
                         args=ActionResearchArgs(tech=entities["tec-a"], team=team)).applyCommit(1, 100)
    makeAction(ActionResearchStart,state=state, entities=entities,
                        args=ActionResearchArgs(tech=entities["tec-c"], team=team)).applyCommit(1, 100)
    makeAction(ActionResearchFinish, state=state, entities=entities,
                         args=ActionResearchArgs(tech=entities["tec-c"], team=team)).applyCommit(1, 100)
    makeAction(ActionResearchStart,state=state, entities=entities,
                        args=ActionResearchArgs(tech=entities["tec-d"], team=team)).applyCommit(1, 100)


    teamState = state.teamStates[team]

    expected = {entities["tec-start"], entities["tec-a"], entities["tec-c"]}
    diff = teamState.techs.symmetric_difference(expected)
    assert len(diff) == 0
    assert len(teamState.researching) == 1
    assert entities["tec-d"] in teamState.researching


def test_bonusCheapDie():
    entities = TEST_ENTITIES
    state = createTestInitState()
    state.teamStates[team].techs.add(entities["tec-maso"])
    state.teamStates[team].researching.add(entities["tec-slon"])

    args = ActionResearchArgs(tech=entities["tec-slon"], team=team)
    action = makeAction(ActionResearchFinish, state=state, entities=entities, args=args)

    assert action.cost() == {}

    action.applyCommit(1, 100)

    assert state.teamStates[team].throwCost == 8


def test_bonusObyvatel():
    entities = TEST_ENTITIES
    state = createTestInitState()
    state.teamStates[team].researching.add(entities["tec-slon"])

    args = ActionResearchArgs(tech=entities["tec-slon"], team=team)
    action = makeAction(ActionResearchFinish, state=state, entities=entities, args=args)

    before = state.teamStates[team].granary.get(entities.basicFoodProduction, 0)
    result = action.applyCommit(1, 100)

    assert state.teamStates[team].resources[entities.obyvatel] == 120
    assert state.teamStates[team].granary[entities.basicFoodProduction] == before + 1
