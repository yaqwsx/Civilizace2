from game.actions.nextTurn import ActionNextTurn, ActionNextTurnArgs
from game.actions.researchStart import ActionResearchStart, ActionResearchStartArgs
from game.entities import Entities
from game.state import GameState
from game.tests.actions.common import TEST_ENTITIES, TEST_TEAMS

import pytest

def test_startOnce():
    entities = TEST_ENTITIES
    state = GameState.createInitial(TEST_TEAMS, entities)
    tech = entities["tech-a"]
    
    assert len(state.teamStates["tym-zeleny"].researching) == 0

    args = ActionResearchStartArgs(tech = tech, team="tym-zeleny")
    action = ActionResearchStart(state = state, entities = entities, args = args)

    cost = action.cost()
    assert len(cost.resources) == 0
    assert len(cost.allowedDice) == 1

    action.commit()

    researching = state.teamStates["tym-zeleny"].researching
    assert len(researching) == 1
    assert tech in researching

