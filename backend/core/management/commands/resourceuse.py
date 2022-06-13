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


def prettyprint(resources: Dict[Resource, Decimal]):
    return ", ".join([f"{amount}x {resource.name}" for resource, amount in resources.items()])
        

class Command(BaseCommand):
    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)

    def add_arguments(self, parser):
        parser.add_argument("name")

    def handle(self, name, *args, **kwargs):
        
        targetFile = settings.ENTITY_PATH / setFilename("GAME")
        entities = loadEntities(targetFile)

        print("MATERIAL used in:")
        material = entities["mat-" + name]
        for vyroba in entities.vyrobas.values():
            if material in vyroba.cost:
                print(f"  {vyroba.cost[material]}x in {vyroba.name}: {prettyprint(vyroba.cost)}")
        
        print("MATERIAL created by:")
        material = entities["mat-" + name]
        for vyroba in entities.vyrobas.values():
            if material == vyroba.reward[0]:
                print(f"  {vyroba.reward[1]}x from {vyroba.name}: {prettyprint(vyroba.cost)}")

        print("PRODUCTION used in:")
        material = entities["pro-" + name]
        for vyroba in entities.vyrobas.values():
            if material in vyroba.cost:
                print(f"  {vyroba.cost[material]}x in {vyroba.name}: {prettyprint(vyroba.cost)}")
        
        print("PRODUCTION created by:")
        material = entities["pro-" + name]
        for vyroba in entities.vyrobas.values():
            if material == vyroba.reward[0]:
                print(f"  {vyroba.reward[1]}x from {vyroba.name}: {prettyprint(vyroba.cost)}")
