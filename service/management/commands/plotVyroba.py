from django.core.management import BaseCommand
from game.data.vyroba import VyrobaModel, EnhancementModel
from service.plotting import vyroby
import sys

class Command(BaseCommand):
    help = "Draw vyrobas"

    def add_arguments(self, parser):
        parser.add_argument("--buildDir", type=str, default="_build/vyrobas",
            help="Build directory" )
        parser.add_argument("--demo", action='store_true', help="Build only one vyroba and one enhancement" )

    def handle(self, *args, **kwargs):
        buildDir = kwargs["buildDir"]
        builder = vyroby.VyrobaBuilder(buildDir, "game/static/icons")
        if kwargs.get("demo", False):
            print("Running in demo mode, building tech-les, build-pila")
            builder.generateVyrobaLabel(VyrobaModel.objects.get(id="vyr-vcelar"))
            builder.generateVyrobaLabel(VyrobaModel.objects.get(id="vyr-most"))

            builder.generateEnhancementLabel(EnhancementModel.objects.get(id="enh-destilace"))
            builder.generateEnhancementLabel(EnhancementModel.objects.get(id="enh-kotel"))
            return
        print("Building vyrobas...", end="")
        builder.generateVyrobaLabels()
        print(" Done")

        print("Building enhancements...", end="")
        builder.generateEnhancementLabels()
        print(" Done")

        print("Building sheets...", end="")
        builder.fullSheet()
        builder.emptySheet()
        print(" Done")






