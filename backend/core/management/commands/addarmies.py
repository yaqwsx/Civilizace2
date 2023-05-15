from argparse import ArgumentParser
from game.state import Army, GameState
from django.core.management import BaseCommand




armyNames = ["A", "B", "C", "D", "E", "F", "G"]

def addArmies(state: GameState):
    assert len(state.map.armies) % 8 == 0
    currentCount = len(state.map.armies)
    name = armyNames[round(currentCount/8)]
    for i, team in enumerate(state.teamStates.keys()):
        army = Army(
            team = team,
            index = currentCount + i,
            name = name,
            level = 1
        )
        state.map.armies.append(army)


class Command(BaseCommand):
    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)

    def add_arguments(self, parser: ArgumentParser):
        parser.add_argument("targetcount")

    def handle(self, targetcount, *args, **kwargs):
        raise NotImplementedError("Not finished yet")
        state = None
        assert len(state.map.armies) == 8*(targetcount+1)
        addArmies(state)
        None
