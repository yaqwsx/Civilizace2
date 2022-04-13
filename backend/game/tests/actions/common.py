from html import entities
from game import entityParser
from game.entities import Resource, Entities, Tech, Vyroba
from game.state import GameState, TeamId
from decimal import Decimal
from typing import List

D = Decimal

TEST_DATA_RESOURCES = {
    ("res-prace", "Práce"),
    ("res-obyvatel", "Obyvatelé"),
    ("mat-drevo", "Dřevo"),
    ("mat-kamen", "Kámen"),
    ("prod-drevo", "Dřevorubec"),
    ("prod-kamen", "Kameník")
}

TEST_DATA_TECH = [
    ("tech-start", 10, {"tech-a": "die-hory", "tech-b": "die-les", "tech-c": "die-plan"}),
    ("tech-a", 20, {"tech-b": "die-hory"}),
    ("tech-b", 30, {}),
    ("tech-c", 40, {"tech-d": "die-plan"}),
    ("tech-d", 42, {})
]

TEST_DATA_VYROBA = [
    ("vyr-drevo", {"res-prace": 10}, "mat-drevo", 2, "die-les", 5),
    ("vyr-drevo-prod", {"res-prace": 10, "res-obyvatel": 5}, "prod-drevo", 2, "die-les", 10)
]


def addResources(entities, data=TEST_DATA_RESOURCES):
    return {entry[0] : Resource(id=entry[0], name=entry[1]) for entry in data}


def addVyrobas(entities, data=TEST_DATA_VYROBA):
    vyrobas = []
    for vyroba in data:
        id = vyroba[0]
        reward = entities[vyroba[2]]
        amount = vyroba[3]
        cost = {entities[item[0]]: item[1] for item in vyroba[1].items()}
        vyrobas.append(Vyroba(id=id, name=id.upper(), cost=cost, 
                              die=vyroba[4], diePoints=vyroba[5], 
                              reward=reward, rewardAmount=amount))
    entities.update({v.id : v for v in vyrobas})
    return entities

def addTechs(entities, data=TEST_DATA_TECH):
    techs = {}
    for techData in data:
        techs[techData[0]] = Tech(
            id=techData[0],
            name=techData[0].upper(),
            cost={},
            diePoints=techData[1],
            edges={})

    for techData in data:
        tech = techs[techData[0]]
        for edge in techData[2].items():
            target = techs[edge[0]]
            tech.edges[target] = edge[1]

    print("Techs: " + str(techs))
    entities.update(techs)
    return entities


#TEST_ENTITIES = Entities(
#    addTechs(addVyrobas(addResources({}))).values())

TEST_TEAM_ID = "tym-zeleny"

TEST_ENTITIES = entityParser.EntityParser("backend\\testEntities.json").parse()

def createTestInitState(entities=TEST_ENTITIES):
    state = GameState.createInitial(TEST_TEAMS, entities)
    state.teamStates[TEST_TEAM_ID].researching.add(entities["tec-c"])
    return state


TEST_TEAMS: List[TeamId] = ["tym-zeleny", "tym-modry"]

