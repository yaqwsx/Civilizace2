from collections import Counter
from pathlib import Path
import json
import sys
from django.core.management import BaseCommand

from core.gsheets import getSheets
from game.entityParser import EntityParser
from django.conf import settings

TASK_SETS = {
    "GAME": "1QO0p1Fquxp7u3CulvPwaFO-zF2q9mtI8LAHFeVJyu_A",
    "TEST": "1IuPKQL3WnyENYIR9AV7Ti1c5b6AcwfBtm10NNzUGZqU"
}

def setFilename(name):
    return f"{name}.json"

def pullEntityTable(id):
    sheets = getSheets(id)
    data = {sheet.title: sheet.get_all_values() for sheet in sheets.worksheets()}
    return data


class Command(BaseCommand):

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)

    def handle(self, *args, **options):
        settings.TASK_PATH.mkdir(parents=True, exist_ok=True)
        for name, id in TASK_SETS.items():
            try:
                targetFile = settings.TASK_PATH / setFilename(name)
                print(f"Pulling tasks {name} to file {targetFile}")
                sheets = getSheets(id)
                data = {sheet.title: sheet.get_all_values() for sheet in sheets.worksheets()}
                with open(targetFile, "w") as f:
                    json.dump(data, f)
            except RuntimeError as e:
                sys.exit("ERROR: Failed to save tasks. Cause: {}".format(e.args[0]))
