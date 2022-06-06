from game.actionsNew.vyroba import ActionVyroba, ActionVyrobaArgs
from game.tests.actions.common import TEST_ENTITIES, TEAM_ADVANCED, createTestInitState

teamId = TEAM_ADVANCED


def test_initiate():
    entities = TEST_ENTITIES
    state = createTestInitState()
    team = state.teamStates[teamId]
    originalResources = team.resources.copy()

    args = ActionVyrobaArgs(
        vyroba = entities["vyr-drevo1Mat"],
        count = 1,
        tile = team.homeTile.entity,
        plunder = False,
        team = teamId
    )
    action = ActionVyroba(state=state, entities=entities, args=args)

    result = action.applyInitiate()
    assert team.resources[entities["res-prace"]] == 90

    result = action.revertInitiate()
    assert team.resources[entities["res-prace"]] == 100

    args.count = 5
    action =  ActionVyroba(state=state, entities=entities, args=args)

    result = action.applyInitiate()
    assert team.resources[entities["res-prace"]] == 50

    result = action.revertInitiate()
    assert team.resources[entities["res-prace"]] == 100

    args.vyroba = entities["vyr-drevo1Pro"]
    action =  ActionVyroba(state=state, entities=entities, args=args)

    result = action.applyInitiate()
    assert team.resources[entities["res-prace"]] == 50
    assert team.resources[entities["res-obyvatel"]] == 90

    result = action.revertInitiate()
    assert team.resources[entities["res-obyvatel"]] == 100

    assert team.resources == originalResources


def test_simple():
    entities = TEST_ENTITIES
    state = createTestInitState()
    team = state.teamStates[teamId]
    originalResources = team.resources.copy()

    args = ActionVyrobaArgs(
        vyroba = entities["vyr-drevo1Mat"],
        count = 1,
        tile = team.homeTile.entity,
        plunder = False,
        team = teamId
    )
    action = ActionVyroba(state=state, entities=entities, args=args)

    initResult = action.applyInitiate()
    commitResult = action.applyCommit(1, 5)

    assert team.resources == {entities["res-prace"]:80, entities["res-obyvatel"]:100, entities["pro-drevo"]: 20}
    assert "Vydejte týmu" in commitResult.message
    assert "Tým obdržel" in commitResult.message


def test_production():
    entities = TEST_ENTITIES
    state = createTestInitState()
    team = state.teamStates[teamId]
    originalResources = team.resources.copy()

    args = ActionVyrobaArgs(
        vyroba = entities["vyr-drevo1Pro"],
        count = 1,
        tile = team.homeTile.entity,
        plunder = False,
        team = teamId
    )
    action = ActionVyroba(state=state, entities=entities, args=args)

    initResult = action.applyInitiate()
    commitResult = action.applyCommit(1, 5)

    assert team.resources == {entities["res-prace"]:80, entities["res-obyvatel"]:98, entities["pro-drevo"]: 21}
    assert "Vydejte týmu" not in commitResult.message
    assert "Tým obdržel" in commitResult.message


def test_distance():
    entities = TEST_ENTITIES
    state = createTestInitState()
    team = state.teamStates[teamId]

    args = ActionVyrobaArgs(
        vyroba = entities["vyr-drevo1Mat"],
        count = 1,
        tile = entities["map-tile06"],
        plunder = False,
        team = teamId
    )
    action = ActionVyroba(state=state, entities=entities, args=args)

    distance = action.requiresDelayedEffect()

    assert distance == 600