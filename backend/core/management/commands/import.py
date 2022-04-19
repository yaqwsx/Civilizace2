from collections import Counter
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

    return data
    
def checkAndSave(data, fileName):
    parser = EntityParser(data)
    entities = parser.parse()
    
    if (len(parser.errors)) > 0:
        for message in parser.errors:
            print("  " + message)
        raise RuntimeError("Failed to validate entities. Errors listed above")

    print()
    c = Counter([x[:3] for x in entities.keys()])
    for x in ["tymy", "natuaral resources", "types of resources", "map tiles", "buildings", "resourses", "materials", "productions", "techs", "vyrobas"]:
        print("    " + x + ": " + str(c[x[:3]]))
    print("SUCCESS: Created " + str(len(entities)) + " entities from " + fileName)

    with open(fileName, "w") as file:
        json.dump(data, file)
    
    print("Data saved to file {}".format(fileName))


class Command(BaseCommand):

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)

    def handle(self, *args, **options):
        for item in ENTITY_SETS.items():
            try:
                print("Importing world " + item[0] + " to file " + item[1][1])
                data = importEntities(item[1])
                checkAndSave(data, item[1][1])
            except RuntimeError as e:
                print("ERROR: Failed to save entities. Cause: {}".format(e.args[0]))