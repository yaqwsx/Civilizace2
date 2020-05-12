from django.core.management import BaseCommand
from game.models.state import State, GenerationWorldState
import game.data as data
import json

class Command(BaseCommand):

    def handle(self, *args, **options):
        updater = data.Update()
        warnings = updater.download()

        if len(warnings):
            print(warnings[0])
            for line in warnings[1:]:
                print("  " + line)



