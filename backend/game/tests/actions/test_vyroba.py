from game.actions.common import ActionArgumentException, ActionCost
from game.actions.nextTurn import ActionNextTurn, ActionNextTurnArgs
from game.actions.researchFinish import ActionResearchFinish
from game.actions.researchStart import ActionResearchStart, ActionResearchArgs
from game.actions.vyroba import ActionVyroba, ActionVyrobaArgs
from game.entities import Entities
from game.state import GameState
from game.tests.actions.common import TEST_ENTITIES, TEST_TEAM, createTestInitState

import pytest

teamId = TEST_TEAM


def test_vyroba_initial():
    entities = TEST_ENTITIES
    state = createTestInitState()
    
    prod = entities["vyr-drevo1Pro"]
    assert entities["res-obyvatel"] in prod.cost
    assert prod.cost[entities["res-obyvatel"]] == 2
