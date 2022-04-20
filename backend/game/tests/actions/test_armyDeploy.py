import pytest
from game.actions.armyDeploy import ActionArmyDeploy
from game.actions.common import ActionException
from game.state import Army, ArmyId, ArmyState
from game.tests.actions.common import TEAM_BASIC
from testing import PYTEST_COLLECT, reimport

if not PYTEST_COLLECT:
    from game.tests.actions.common import TEST_ENTITIES, createTestInitState
    from game.actions.armyDeploy import ActionArmyDeployArgs, ArmyGoal


def test_cost():
    reimport(__name__)

    state = createTestInitState()
    entities = TEST_ENTITIES

    team = TEAM_BASIC
    armyId = ArmyId(team=team, prestige=15)
    tile = entities["map-tile04"]

    args = ActionArmyDeployArgs(army=armyId, tile=tile, team=team, goal=ArmyGoal.Occupy, equipment=10)
    action = ActionArmyDeploy(args=args, entities=entities, state=state)

    cost = action.cost()
    assert cost.resources == {entities.zbrane: 10}, "Requires {} (exp. {})".format(cost.resources, entities.zbrane)
    assert cost.postpone == 10, "Deploying {} to tile {} should take 10 minutes (act={})"\
        .format(armyId, tile, cost.postpone)
    

def test_commit():
    reimport(__name__)

    state = createTestInitState()
    entities = TEST_ENTITIES

    team = TEAM_BASIC
    armyId = ArmyId(team=team, prestige=15)
    tile = entities["map-tile04"]

    args = ActionArmyDeployArgs(army=armyId, tile=tile, team=team, goal=ArmyGoal.Occupy, equipment=10)
    action = ActionArmyDeploy(args=args, entities=entities, state=state)
    result = action.commit()

    army = state.teamStates[team].armies[armyId]
    exp = Army(team=team, prestige=15, equipment=10, tile=tile, state=ArmyState.Marching)
    assert army == exp, "Army in unexpected state:\n\nEXPECTED: {}\n\nACTUAL:  {}\n".format(exp, army)


def test_invalidArgs():
    reimport(__name__)

    state = createTestInitState()
    entities = TEST_ENTITIES

    team = TEAM_BASIC
    armyId = ArmyId(team=team, prestige=15)
    tile = entities["map-tile04"]

    args = ActionArmyDeployArgs(army=armyId, tile=tile, team=team, goal=ArmyGoal.Occupy, equipment=11)
    action = ActionArmyDeploy(args=args, entities=entities, state=state)
    with pytest.raises(ActionException) as einfo:
        action.cost()
        action.commit()

    args = ActionArmyDeployArgs(army=armyId, tile=tile, team=team, goal=ArmyGoal.Occupy, equipment=-1)
    action = ActionArmyDeploy(args=args, entities=entities, state=state)
    with pytest.raises(ActionException) as einfo:
        action.cost()
        action.commit()
