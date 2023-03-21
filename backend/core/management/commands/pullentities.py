from argparse import ArgumentParser
from collections import Counter
from os import PathLike
import json
import sys
from django.core.management import BaseCommand
from core.gsheets import getSheets
from django.conf import settings

from game.entityParser import ErrorHandler, EntityParser, ParserError

ENTITY_SETS = {
    "GAME": "1ZNjrkBA6na8_aQVPBheqjRO5vMbevZR38AYCYVyLqh0",
    "TEST": "1d-d_cCsee7IZd7ZRhnRGMpKaWbjCA6pl-fU-3yYpvKw"
}

def setFilename(name: str) -> str:
    return f"{name}.json"

def pullEntityTable(id: str) -> dict[str, list[list[str]]]:
    sheets = getSheets(id)
    data = {sheet.title: sheet.get_all_values() for sheet in sheets.worksheets()}
    return data

def checkAndSave(data: dict[str, list[list[str]]],
                 fileName: str | PathLike[str],
                 err_handler: ErrorHandler = ErrorHandler(),
                 ):
    entities = EntityParser.parse(data, err_handler=err_handler)
    assert err_handler.success()

    counter = Counter([x[:3] for x in entities.keys()])
    for x in ["tymy", "orgove", "natuaral resources", "types of resources", "map tiles", "buildings", "resourses", "materials", "productions", "mge-generic materials", "pge-generic productions", "techs", "vyrobas"]:
        print(f"    {x}: {counter[x[:3]]}")
    print(f"SUCCESS: Created {len(entities)} entities from {fileName}")

    with open(fileName, "w") as file:
        json.dump(data, file)

    print("Data saved to file {}".format(fileName))

def trySave(name, id: str, err_handler: ErrorHandler = ErrorHandler()):
    try:
        targetFile = settings.ENTITY_PATH / setFilename(name)
        print(f"Pulling world {name} to file {targetFile}")
        data = pullEntityTable(id)
        checkAndSave(data, targetFile, err_handler=err_handler)
    except Exception as e:
        sys.exit(f"ERROR: Failed to save entities {name}. Cause: {e.__repr__()}")


class Command(BaseCommand):

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)

    def add_arguments(self, parser: ArgumentParser):
        # Optional argument
        parser.add_argument('-s', '--set', type=str, choices=list(ENTITY_SETS), nargs='+', default=list(ENTITY_SETS))
        parser.add_argument('--no-warn', action='store_true')
        parser.add_argument('--max-errs', type=int, default=5)

    def handle(self, *args, **options):
        settings.ENTITY_PATH.mkdir(parents=True, exist_ok=True)

        for entity_set in options["set"]:
            assert entity_set in ENTITY_SETS
            trySave(entity_set,
                    ENTITY_SETS[entity_set],
                    ErrorHandler(max_errs=options["max_errs"], no_warn=options["no_warn"]),
                    )
