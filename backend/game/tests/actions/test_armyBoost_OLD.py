# import pytest
# from game.actions.armyBoost import ActionBoost, ActionBoostArgs
# from game.actions.armyDeploy import ArmyDeployAction, ArmyDeployArgs, ArmyGoal
# from game.actions.common import ActionException
# from game.state import Army, ArmyId, ArmyState
# from game.tests.actions.common import TEAM_BASIC, TEST_ENTITIES, createTestInitState


# def test_boost():
#     state = createTestInitState()
#     entities = TEST_ENTITIES
#     team = TEAM_BASIC
#     armyId = ArmyId(team=team, prestige=15)
#     army = state.teamStates[team].armies[armyId]
#     tile = entities["map-tile04"]

#     ArmyDeployAction(args=ArmyDeployArgs(army=armyId, tile=tile, team=team, goal=ArmyGoal.Occupy, equipment=10), entities=entities, state=state)\
#         .commit()

#     action = ActionBoost(args=ActionBoostArgs(team=team, prestige=armyId.prestige, boost=2), entities=entities, state=state)

#     assert army.boost < 0, "Unboosted army {} should have negative boost value".format(army)
#     action.commit()
#     assert army.boost == 2, "Failed to boost army {}".format(army)

# def test_timedOut():
#     state = createTestInitState()
#     entities = TEST_ENTITIES
#     team = TEAM_BASIC
#     armyId = ArmyId(team=team, prestige=15)
#     army = state.teamStates[team].armies[armyId]
#     tile = entities["map-tile04"]

#     action = ActionBoost(args=ActionBoostArgs(team=team, prestige=armyId.prestige, boost=2), entities=entities, state=state)

#     with pytest.raises(ActionException) as einfo:
#         # Army is not marching towards a tile
#         action.commit()

#     ArmyDeployAction(args=ArmyDeployArgs(army=armyId, tile=tile, team=team, goal=ArmyGoal.Occupy, equipment=10), entities=entities, state=state)\
#         .commit()
#     ActionBoost(args=ActionBoostArgs(team=team, prestige=armyId.prestige, boost=2), entities=entities, state=state)\
#         .commit()

#     with pytest.raises(ActionException) as einfo:
#         # boost for second time
#         action = ActionBoost(args=ActionBoostArgs(team=team, prestige=armyId.prestige, boost=2), entities=entities, state=state)
#         action.commit()


