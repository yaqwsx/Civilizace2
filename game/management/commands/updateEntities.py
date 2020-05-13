from django.core.management import BaseCommand
from game.models.state import State, GenerationWorldState
import game.data as data
import json

from game.data.update import Update, UpdateError

class Command(BaseCommand):
    help = "Update entities"
    defaultFile = "game/data/entities.json"

    def add_arguments(self, parser):
        parser.add_argument("--sourceFile", type=str, help="Instead of downloading, read entities from file")
        parser.add_argument("--cacheFile", type=str, help="After successful update, store entities to given file")

    def handle(self, *args, **kwargs):
        sourceFile = kwargs["sourceFile"]
        cacheFile = kwargs["cacheFile"]

        updater = Update()
        if sourceFile:
            print("Using {} as update source".format(sourceFile))
            updater.fileAsSource(sourceFile)
        else:
            print("Using google spreadsheet as source")
            updater.googleAsSource()

        try:
            updater.update()
            print("Update done")
            if not cacheFile:
                cacheFile = self.defaultFile
            updater.saveToFile(cacheFile)
            print("Saved to cache file {}".format(cacheFile))
        except UpdateError as e:
            print("There were some warnings during processing:")
            print(e.warnings[0])
            for line in e.warnings[1:]:
                print("  " + line)




