from game.actions.common import ActionArgumentException, ActionCost
from game.actions.nextTurn import ActionNextTurn, ActionNextTurnArgs
from game.actions.researchFinish import ActionResearchFinish
from game.actions.researchStart import ActionResearchStart, ActionResearchArgs
from game.entities import Entities
from game.state import GameState
from game.tests.actions.common import TEST_ENTITIES, TEST_TEAM_ID, TEST_TEAMS, createTestInitState

import pytest

teamId = TEST_TEAM_ID


def test_initialState():
    entities = TEST_ENTITIES
    state = createTestInitState()

    assert len(state.teamStates[teamId].researching) == 1
    assert len(state.teamStates[teamId].techs) == 1
    assert entities["tech-start"] in state.teamStates[teamId].techs


def test_start():
    entities = TEST_ENTITIES
    state = createTestInitState()
    tech = entities["tech-a"]

    action = ActionResearchStart(
        state=state, entities=entities, teamId=teamId, args=ActionResearchArgs(tech=tech))

    cost = action.cost()
    assert len(cost.resources) == 0
    assert len(cost.allowedDice) == 1

    action.commit()

    researching = state.teamStates[teamId].researching
    assert len(researching) == 2
    assert tech in researching

    action = ActionResearchStart(
        state=state, entities=entities, teamId=teamId, args=ActionResearchArgs(tech=tech))


def test_startOwned():
    entities = TEST_ENTITIES
    state = createTestInitState()

    action = ActionResearchStart(
        state=state, entities=entities, teamId=teamId, args=ActionResearchArgs(tech=entities["tech-start"]))

    with pytest.raises(ActionArgumentException) as einfo:
        action.cost()
    with pytest.raises(ActionArgumentException) as einfo:
        action.commit()


def test_startInProgress():
    entities = TEST_ENTITIES
    state = createTestInitState()

    action = ActionResearchStart(
        state=state, entities=entities, teamId=teamId, args=ActionResearchArgs(tech=entities["tech-c"]))

    with pytest.raises(ActionArgumentException) as einfo:
        action.cost()
    with pytest.raises(ActionArgumentException) as einfo:
        action.commit()


def test_finish():
    entities = TEST_ENTITIES
    state = createTestInitState()
    tech = entities["tech-c"]

    action = ActionResearchFinish(state=state, entities=entities,
                                  teamId=teamId, args=ActionResearchArgs(tech=tech))

    assert action.cost() == ActionCost()

    action.commit()
    assert len(state.teamStates[teamId].researching) == 0
    assert len(state.teamStates[teamId].techs) == 2
    assert tech in state.teamStates[teamId].techs


def test_finishOwned():
    entities = TEST_ENTITIES
    state = createTestInitState()

    action = ActionResearchFinish(state=state, entities=entities,
                                  teamId=teamId, args=ActionResearchArgs(tech=entities["tech-start"]))
    with pytest.raises(ActionArgumentException) as einfo:
        action.commit()


def test_finishUnknown():
    entities = TEST_ENTITIES
    state = createTestInitState()

    action = ActionResearchFinish(state=state, entities=entities,
                                  teamId=teamId, args=ActionResearchArgs(tech=entities["tech-a"]))
    with pytest.raises(ActionArgumentException) as einfo:
        action.commit()


def test_compound():
    entities = TEST_ENTITIES
    state = createTestInitState()

    ActionResearchStart(state=state, entities=entities, teamId=teamId,
                        args=ActionResearchArgs(tech=entities["tech-a"])).commit()
    ActionResearchFinish(state=state, entities=entities, teamId=teamId,
                         args=ActionResearchArgs(tech=entities["tech-a"])).commit()
    ActionResearchFinish(state=state, entities=entities, teamId=teamId,
                         args=ActionResearchArgs(tech=entities["tech-c"])).commit()
    ActionResearchStart(state=state, entities=entities, teamId=teamId,
                        args=ActionResearchArgs(tech=entities["tech-d"])).commit()

    team = state.teamStates[teamId]

    expected = {entities["tech-start"], entities["tech-a"], entities["tech-c"]}
    diff = team.techs.symmetric_difference(expected)
    assert len(diff) == 0
    assert len(team.researching) == 1
    assert entities["tech-d"] in team.researching
