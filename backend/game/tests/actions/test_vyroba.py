from game.actions.common import ActionArgumentException, ActionCost
from game.actions.nextTurn import ActionNextTurn, ActionNextTurnArgs
from game.actions.researchFinish import ActionResearchFinish
from game.actions.researchStart import ActionResearchStart, ActionResearchArgs
from game.actions.vyroba import ActionVyroba, ActionVyrobaArgs
from game.entities import Entities
from game.state import GameState
from game.tests.actions.common import TEST_ENTITIES, TEST_TEAM_ID, TEST_TEAMS, createTestInitState

import pytest

teamId = TEST_TEAM_ID


def test_vyroba_initial():
    entities = TEST_ENTITIES
    state = createTestInitState()
    
    drevo = entities["vyr-drevo"]
    assert drevo.name == drevo.id.upper()

    prod = entities["vyr-drevo-prod"]
    assert prod.name == prod.id.upper()
    assert entities["res-obyvatel"] in prod.cost
    assert prod.cost[entities["res-obyvatel"]] == 5

    e = {item[0] : item[1] for item in entities.items()}
    assert 0 == 0
