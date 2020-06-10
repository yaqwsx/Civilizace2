from django.core.management import BaseCommand
from game.data.tech import TechModel
from service.plotting import tech
import sys

class Command(BaseCommand):
    help = "Draw tech tree"

    def add_arguments(self, parser):
        parser.add_argument("--buildDir", type=str, default="_build",
            help="Build directory" )
        parser.add_argument("--demo", action='store_true', help="Build only one building and one tech" )

    def handle(self, *args, **kwargs):
        buildDir = kwargs["buildDir"]
        builder = tech.TechBuilder(buildDir, "game/static/icons")
        if kwargs.get("demo", False):
            print("Running in demo mode, building tech-les, build-pila")
            builder.generateTechLabel(TechModel.objects.get(id="tech-les"))
            builder.generateTechLabel(TechModel.objects.get(id="build-pila"))
            return
        print("Building labels...", end="")
        builder.generateTechLabels()
        print(" Done")

        print("Building graph...", end="")
        builder.generateFullGraph()
        print(" Done")






