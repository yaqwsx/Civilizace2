from django.core.management import BaseCommand
from game.plague import getDeathToll, simulatePlague



from game.state import PlagueStats

class Command(BaseCommand):
    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)

    def add_arguments(self, parser):
        parser.add_argument("population", type=int)
        parser.add_argument("rounds", type=int)

    def handle(self, population, rounds, *args, **kwargs):
        state = PlagueStats()

        for i in range(rounds):
            nextstat, dead = simulatePlague(state, population)
            population = max(0, population - dead)

            cured = nextstat.immune - state.immune
            infected = nextstat.sick - state.sick + cured + dead
            print(f"Expected death toll: {getDeathToll(nextstat, population)}")
            print(f"{i}: Pop={population}, sick={nextstat.sick}, infected={infected}, cured={cured}, dead={dead}")

            state = nextstat

