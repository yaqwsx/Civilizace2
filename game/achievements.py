
# Definition of achievement logic, each function takes a state and team and
# returns whether given achievement is granted or not

from game.models.state import TechStatusEnum

def greatCounter(state, team):
    teamState = state.teamState(team.id)
    return teamState.sandbox.data["counter"] > 42

def fingers(state, team):
    teamState = state.teamState(team.id)
    return teamState.techs.getStatus("build-pila") == TechStatusEnum.OWNED