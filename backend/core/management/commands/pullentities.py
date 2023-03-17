from collections import Counter
from pathlib import Path
import json
import sys
from django.core.management import BaseCommand

from core.gsheets import getSheets
from game.entityParser import EntityParser
from django.conf import settings

from game.plague import readPlagueFromEntities

ENTITY_SETS = {
    "GAME": "1ZNjrkBA6na8_aQVPBheqjRO5vMbevZR38AYCYVyLqh0",
    "TEST": "1d-d_cCsee7IZd7ZRhnRGMpKaWbjCA6pl-fU-3yYpvKw"
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

def trySave(name, id):
    try:
        targetFile = settings.ENTITY_PATH / setFilename(name)
        print(f"Pulling world {name} to file {targetFile}")
        data = pullEntityTable(id)
        readPlagueFromEntities(data)
        checkAndSave(data, targetFile)
    except RuntimeError as e:
        sys.exit("ERROR: Failed to save entities. Cause: {}".format(e.args[0]))


class Command(BaseCommand):

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)

    def add_arguments(self, parser):
            # Optional argument
            parser.add_argument('-s', '--set', type=str, nargs='+')

    def handle(self, *args, **options):
        settings.ENTITY_PATH.mkdir(parents=True, exist_ok=True)

        if e := options.get("set", None):
            e = e[0]
            trySave(e, ENTITY_SETS[e])
            return

        for name, id in ENTITY_SETS.items():
            trySave(name, id)
