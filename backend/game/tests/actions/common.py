from game.entities import Resource, Entities, Tech
from game.state import TeamId
from decimal import Decimal
from typing import List

D = Decimal

TEST_DATA_RESOURCES = {
    ("res-prace", "Práce"),
    ("res-obyvatel", "Obyvatelé"),
    ("mat-drevo", "Dřevo"),
    ("mat-kamen", "Kámen")
}

TEST_DATA_TECH = [
    ("tech-start", 10, {"tech-a" : "die-hory", "tech-b": "die-les"}),
    ("tech-a", 20, {"tech-b": "die-hory"}),
    ("tech-b", 30, {})
]

def getResources(data = TEST_DATA_RESOURCES):
    return [Resource(id=entry[0], name=entry[1]) for entry in data]

def getTechs(data = TEST_DATA_TECH):
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
    return techs.values()

TEST_ENTITIES = Entities(
        getResources() 
        + list(getTechs(TEST_DATA_TECH)))


TEST_TEAMS: List[TeamId] = ["tym-zeleny", "tym-modry"]
