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

        print()
        print()
        matPrefix = "mge-" if "-" in name else "mat-"
        prodPrefix = "pge-" if "-" in name else "pro-"
        print("TECH MATERIAL usage:")
        material = entities[matPrefix + name]
        for vyroba in entities.techs.values():
            if material in vyroba.cost:
                print(f"  {vyroba.cost[material]}x in {vyroba.name} ({vyroba.points}P): {prettyprint(vyroba.cost)}")

        print()
        print("MATERIAL used in:")
        material = entities[matPrefix + name]
        for vyroba in entities.vyrobas.values():
            if material in vyroba.cost:
                print(f"  {vyroba.cost[material]}x in {vyroba.name} ({vyroba.points}P): {prettyprint(vyroba.cost)}  =>  {vyroba.reward}        Tech: {vyroba.unlockedBy[0][0].name}/{vyroba.unlockedBy[0][1]}")

        print("PRODUCTION used in:")
        material = entities[prodPrefix + name]
        for vyroba in entities.vyrobas.values():
            if material in vyroba.cost:
                print(f"  {vyroba.cost[material]}x in {vyroba.name} ({vyroba.points}P): {prettyprint(vyroba.cost)}  =>  {vyroba.reward}        Tech: {vyroba.unlockedBy[0][0].name}/{vyroba.unlockedBy[0][1]}")
        print()
        print("MATERIAL created by:")
        material = entities[matPrefix + name]
        for vyroba in entities.vyrobas.values():
            if material == vyroba.reward[0]:
                print(f"  {vyroba.reward[1]}x from {vyroba.name} ({vyroba.points}P): {prettyprint(vyroba.cost)}        Tech: {vyroba.unlockedBy[0][0].name}/{vyroba.unlockedBy[0][1]}")

        print("PRODUCTION created by:")
        material = entities[prodPrefix + name]
        for vyroba in entities.vyrobas.values():
            if material == vyroba.reward[0]:
                print(f"  {vyroba.reward[1]}x from {vyroba.name} ({vyroba.points}P): {prettyprint(vyroba.cost)}        Tech: {vyroba.unlockedBy[0][0].name}/{vyroba.unlockedBy[0][1]}")
