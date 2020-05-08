from django.core.management import BaseCommand
from game.models.state import State, GenerationWorldState

class Command(BaseCommand):
    def handle(self, *args, **options):
        print("Hello Django")
        print("Arguments: " + str(options))

        state = State.objects.getNewest()
        generation = state.worldState.generation

        generation.startNextGeneration()
        print("World generation increased")
        print("Current generation = " + str(generation))
        print(str(state.id))
        generation.save()
        state.save()
        print("Current generation = " + str(generation))

        print("Generation update saved, loading from DB")
        state = State.objects.getNewest()
        generation = state.worldState.generation
        print("Current generation DB = " + str(generation))
        print(str(state.id))
