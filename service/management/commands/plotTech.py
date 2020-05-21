from django.core.management import BaseCommand
from game.data.tech import TechModel
from service.plotting import tech
import sys

class Command(BaseCommand):
    help = "Draw tech tree"

    def add_arguments(self, parser):
        parser.add_argument("--buildDir", type=str, default="_build",
            help="Build directory" )

    def handle(self, *args, **kwargs):
        buildDir = kwargs["buildDir"]
        builder = tech.TechBuilder(buildDir)
        print("Building labels...", end="")
        builder.generateTechLabels()
        print(" Done")

        print("Building graph...", end="")
        builder.generateFullGraph()
        print(" Done")






