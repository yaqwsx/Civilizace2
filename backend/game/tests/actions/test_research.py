import pytest

from game.actions.common import ActionFailed
from game.actions.researchFinish import ResearchFinishAction
from game.actions.researchStart import ResearchArgs, ResearchStartAction
from game.tests.actions.common import TEAM_BASIC, TEST_ENTITIES, createTestInitState

teamEntity = TEAM_BASIC


def test_initialState():
    entities = TEST_ENTITIES
    state = createTestInitState()

    assert len(state.teamStates[teamEntity].researching) == 0
    assert len(state.teamStates[teamEntity].techs) == 1
    assert entities.techs["tec-start"] in state.teamStates[teamEntity].techs


def test_start():
    entities = TEST_ENTITIES
    state = createTestInitState()
    tech = entities.techs["tec-a"]

    action = ResearchStartAction.makeAction(
        state=state,
        entities=entities,
        args=ResearchArgs(tech=tech, team=teamEntity),
    )

    cost = action.cost()
    points = action.pointsCost()
    assert cost == tech.cost
    assert points == 20

    action.commitThrows(throws=1, dots=100)

    assert state.teamStates[teamEntity].researching == {tech}


def test_startOwned():
    entities = TEST_ENTITIES
    state = createTestInitState()

    action = ResearchStartAction.makeAction(
        state=state,
        entities=entities,
        args=ResearchArgs(tech=entities.techs["tec-start"], team=teamEntity),
    )

    with pytest.raises(ActionFailed) as einfo:
        action.cost()
    with pytest.raises(ActionFailed) as einfo:
        action.commitThrows(throws=0, dots=0)


def test_startInProgress():
    entities = TEST_ENTITIES
    state = createTestInitState()
    state.teamStates[teamEntity].researching.add(entities.techs["tec-c"])

    action = ResearchStartAction.makeAction(
        state=state,
        entities=entities,
        args=ResearchArgs(tech=entities.techs["tec-c"], team=teamEntity),
    )

    with pytest.raises(ActionFailed) as einfo:
        action.commitThrows(throws=1, dots=100)


def test_finish():
    entities = TEST_ENTITIES
    state = createTestInitState()
    tech = entities.techs["tec-c"]
    state.teamStates[teamEntity].researching.add(entities.techs["tec-c"])

    args = ResearchArgs(tech=tech, team=teamEntity)
    action = ResearchFinishAction.makeAction(state=state, entities=entities, args=args)

    assert action.cost() == {}

    action.commitThrows(throws=1, dots=100)
    assert len(state.teamStates[teamEntity].researching) == 0
    assert len(state.teamStates[teamEntity].techs) == 2
    assert tech in state.teamStates[teamEntity].techs


def test_finishOwned():
    entities = TEST_ENTITIES
    state = createTestInitState()

    action = ResearchFinishAction.makeAction(
        state=state,
        entities=entities,
        args=ResearchArgs(tech=entities.techs["tec-start"], team=teamEntity),
    )
    with pytest.raises(ActionFailed) as einfo:
        action.commitThrows(throws=1, dots=100)


def test_finishUnknown():
    entities = TEST_ENTITIES
    state = createTestInitState()

    action = ResearchFinishAction.makeAction(
        state=state,
        entities=entities,
        args=ResearchArgs(tech=entities.techs["tec-a"], team=teamEntity),
    )
    with pytest.raises(ActionFailed) as einfo:
        action.commitThrows(throws=1, dots=100)


def test_compound():
    entities = TEST_ENTITIES
    state = createTestInitState()

    ResearchStartAction.makeAction(
        state=state,
        entities=entities,
        args=ResearchArgs(tech=entities.techs["tec-a"], team=teamEntity),
    ).commitThrows(throws=1, dots=100)
    ResearchFinishAction.makeAction(
        state=state,
        entities=entities,
        args=ResearchArgs(tech=entities.techs["tec-a"], team=teamEntity),
    ).commitThrows(throws=1, dots=100)
    ResearchStartAction.makeAction(
        state=state,
        entities=entities,
        args=ResearchArgs(tech=entities.techs["tec-c"], team=teamEntity),
    ).commitThrows(throws=1, dots=100)
    ResearchFinishAction.makeAction(
        state=state,
        entities=entities,
        args=ResearchArgs(tech=entities.techs["tec-c"], team=teamEntity),
    ).commitThrows(throws=1, dots=100)
    ResearchStartAction.makeAction(
        state=state,
        entities=entities,
        args=ResearchArgs(tech=entities.techs["tec-d"], team=teamEntity),
    ).commitThrows(throws=1, dots=100)

    teamState = state.teamStates[teamEntity]

    expected = {
        entities.techs["tec-start"],
        entities.techs["tec-a"],
        entities.techs["tec-c"],
    }
    diff = teamState.techs.symmetric_difference(expected)
    assert len(diff) == 0
    assert len(teamState.researching) == 1
    assert entities.techs["tec-d"] in teamState.researching
