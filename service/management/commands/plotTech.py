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
        parser.add_argument("-r", type=int, default=0)
        parser.add_argument("-g", type=int, default=0)
        parser.add_argument("-b", type=int, default=0)

    def handle(self, *args, **kwargs):
        buildDir = kwargs["buildDir"]
        r, g, b = kwargs["r"], kwargs["g"], kwargs["b"]
        builder = tech.TechBuilder(buildDir, "game/static/icons", (r, g, b))
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
        builder.generateEmptyFullGraph()
        print(" Done")






