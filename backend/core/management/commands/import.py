import json
import os
from django.core.management import BaseCommand

from core.gsheets import getSheets
from game.entityParser import EntityParser
from django.conf import settings

ENTITY_SETS = {
    #"GAME": ("1BNdnhzJoF9oSLHvpX_UsEPEROZ6U_nHNLsqNerNWIoA", "entities.json"),
    "TEST": ("1_6Niwfwu896v6qi2B6l4436HzQ2lVwwlwmS1Xo0izQs",
             os.path.join(settings.BASE_DIR, "testEntities.json"))}


def importEntities(id):
    sheets = getSheets(id[0])
    data = {sheet.title: sheet.get_all_values() for sheet in sheets.worksheets()}

    with open(id[1], "w") as file:
        json.dump(data, file)

class Command(BaseCommand):

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)

    def handle(self, *args, **options):
        for item in ENTITY_SETS.items():
            print("Importing world " + item[0] + " to file " + item[1][1])
            importEntities(item[1])

            parser = EntityParser(item[1][1])
            parser.parse()
