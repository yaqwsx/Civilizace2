from argparse import ArgumentParser
from ctypes import ArgumentError
from game.state import Army, GameState
from collections import Counter
from decimal import Decimal
from pathlib import Path
import json
import sys
from typing import Dict
from django.core.management import BaseCommand

from core.gsheets import getSheets
from core.management.commands.pullentities import setFilename
from game.entities import Resource
from game.entityParser import EntityParser, loadEntities
from django.conf import settings

from game.models import DbEntities


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
