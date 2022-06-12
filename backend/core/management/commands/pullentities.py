from collections import Counter
from pathlib import Path
import json
import sys
from django.core.management import BaseCommand

from core.gsheets import getSheets
from game.entityParser import EntityParser
from django.conf import settings

ENTITY_SETS = {
    "GAME": "1BNdnhzJoF9oSLHvpX_UsEPEROZ6U_nHNLsqNerNWIoA",
    "TEST": "1_6Niwfwu896v6qi2B6l4436HzQ2lVwwlwmS1Xo0izQs"
}

def setFilename(name):
    return f"{name}.json"

def pullEntityTable(id):
    sheets = getSheets(id)
    data = {sheet.title: sheet.get_all_values() for sheet in sheets.worksheets()}
    return data

def checkAndSave(data, fileName):
    parser = EntityParser(data)
    entities = parser.parse()

    if (len(parser.errors)) > 0:
        for message in parser.errors:
            print("  " + message)
        raise RuntimeError("Failed to validate entities. Errors listed above")

    c = Counter([x[:3] for x in entities.keys()])
    for x in ["tymy", "orgove", "natuaral resources", "types of resources", "map tiles", "buildings", "resourses", "materials", "productions", "techs", "vyrobas"]:
        print("    " + x + ": " + str(c[x[:3]]))
    print(f"SUCCESS: Created {len(entities)} entities from {fileName}")

    with open(fileName, "w") as file:
        json.dump(data, file)

    print("Data saved to file {}".format(fileName))


class Command(BaseCommand):

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)

    def handle(self, *args, **options):
        settings.ENTITY_PATH.mkdir(parents=True, exist_ok=True)
        for name, id in ENTITY_SETS.items():
            try:
                targetFile = settings.ENTITY_PATH / setFilename(name)
                print(f"Pulling world {name} to file {targetFile}")
                data = pullEntityTable(id)
                checkAndSave(data, targetFile)
            except RuntimeError as e:
                sys.exit("ERROR: Failed to save entities. Cause: {}".format(e.args[0]))
