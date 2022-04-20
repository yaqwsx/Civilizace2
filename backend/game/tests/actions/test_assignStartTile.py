import pytest
from game.state import GameState
from game.actions.common import ActionException
from game.actions.common import ActionCost
from game.actions.assignStartTile import ActionAssignTile, ActionAssignTileArgs
from game.tests.actions.common import createTestInitState
from testing import PYTEST_COLLECT, reimport

if not PYTEST_COLLECT:
    from game.tests.actions.common import TEST_ENTITIES, TEAM_ADVANCED


def test_initialState():
    reimport(__name__)

    entities = TEST_ENTITIES
    state = GameState.createInitial(entities)
    assert len(state.map.tiles) == 24, "Empty map should have 24 tiles"

def test_assignOne():
    reimport(__name__)

    entities = TEST_ENTITIES
    state = GameState.createInitial(entities)

    args = ActionAssignTileArgs(team=TEAM_ADVANCED, index=1)
    action = ActionAssignTile(args=args, state=state, entities=entities)
    assert action.cost() == ActionCost(), "Assigning tile to team should be free"

    assert state.map.getHomeTile(TEAM_ADVANCED) == None, "Team should not have a home tile assigned by default"

    action.commit()
    tile = state.map.getHomeTile(TEAM_ADVANCED)
    assert tile != None, "Assigning tile to team failed"
    assert tile.entity.index == 1, "Assigned tile has wrong index (exp=1, act={})".format(1, tile.entity.index)
    assert len(state.map.tiles) == 25, "Adding a home tile should increase tile count"


def test_assignAll():
    reimport(__name__)

    entities = TEST_ENTITIES
    state = GameState.createInitial(entities)

    for index, team in enumerate(entities.teams.values()):
        args = ActionAssignTileArgs(team=team, index=4*index + 1)
        action = ActionAssignTile(args=args, state=state, entities=entities)
        action.commit()

    assert len(state.map.tiles) == 32, "Adding 8 home tiles should result in 32 tiles in total (act={})".format(len(state.map.tiles))
    assert len(state.map.homeTiles) == 8, "Wrong home tile count (exp=8, act={})".format(len(state.map.homeTiles))

    for index, team in enumerate(entities.teams.values()):
        tile = state.map.getHomeTile(team)
        assert tile != None, "Home tile was not added for team {}".format(team.id)
        assert tile.entity.index == index*4 + 1, "Wrong home tile index for team {} (exp={}, act={})".format(team.id, index*4+1, tile.entity.index)
    
def test_assignDuplicate():
    reimport(__name__)

    entities = TEST_ENTITIES
    state = GameState.createInitial(entities)

    args = ActionAssignTileArgs(team=TEAM_ADVANCED, index=1)
    action = ActionAssignTile(args=args, state=state, entities=entities)
    action.commit()
    args = ActionAssignTileArgs(team=entities["tym-zluti"], index=1)
    action = ActionAssignTile(args=args, state=state, entities=entities)
    with pytest.raises(ActionException) as einfo:
        action.commit()
    
def test_reassingnTeam():
    reimport(__name__)

    entities = TEST_ENTITIES
    state = GameState.createInitial(entities)

    args = ActionAssignTileArgs(team=TEAM_ADVANCED, index=1)
    action = ActionAssignTile(args=args, state=state, entities=entities)
    action.commit()
    args = ActionAssignTileArgs(team=TEAM_ADVANCED, index=5)
    action = ActionAssignTile(args=args, state=state, entities=entities)
    action.commit()

    assert action.errors.message == "", "Reassigning team to different home tile failed:{}".format(action.errors.message)
    assert state.map.tiles.get(1) == None, "Unassigned tile remained on the map: {}".format(state.map.tiles.get(1)) 
    assert state.map.tiles.get(5) != None, "Newly assigned tile #5 does not exist"
    assert state.map.getHomeTile(TEAM_ADVANCED) != None, "Team has no home tile after reassignment"
    assert state.map.getHomeTile(TEAM_ADVANCED).entity.index == 5, "Reassigned team home tile has wrong index {}".format(state.map.getHomeTile(TEAM_ADVANCED).entity.index)

def test_examineTestInitState():
    reimport(__name__)

    entities = TEST_ENTITIES
    state = createTestInitState()

    