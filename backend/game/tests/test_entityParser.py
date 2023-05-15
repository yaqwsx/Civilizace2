from game.tests.actions.common import TEST_ENTITIES

def test_homeTiles():
    entities = TEST_ENTITIES

    for tile in entities.tiles.values():
        teams_home_on_tile = [team for team in entities.teams.values() if team.homeTile == tile]
        assert len(teams_home_on_tile) <= 1


def test_fields():
    entities = TEST_ENTITIES
    assert "Well seasoned" == entities.techs["tec-maso"].flavor
