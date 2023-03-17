from game.tests.actions.common import TEST_ENTITIES, TEAM_ADVANCED, createTestInitState

teamId = TEAM_ADVANCED

def test_homeTiles():
    entities = TEST_ENTITIES

    for team in entities.teams.values():
        assert team.homeTileId != None
        assert entities[team.homeTileId] != None

    for tile in entities.tiles.values():
        teams = [team for team in entities.teams.values() if team.homeTileId == tile.id]
        assert len(teams) <= 1


def test_fields():
    entities = TEST_ENTITIES
    assert "star" in entities["tec-c"].bonuses
    assert "Well seasoned" == entities["tec-maso"].flavor
