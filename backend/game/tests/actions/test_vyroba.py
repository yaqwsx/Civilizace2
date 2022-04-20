from game.tests.actions.common import TEST_ENTITIES, TEAM_ADVANCED, createTestInitState

teamId = TEAM_ADVANCED


def test_vyroba_initial():
    entities = TEST_ENTITIES
    state = createTestInitState()
    
    prod = entities["vyr-drevo1Pro"]
    assert entities["res-obyvatel"] in prod.cost
    assert prod.cost[entities["res-obyvatel"]] == 2
