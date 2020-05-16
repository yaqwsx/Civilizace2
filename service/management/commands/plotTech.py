from django.core.management import BaseCommand
from game.data.tech import TechModel
from service.plotting import dot, tech
import sys

class Command(BaseCommand):
    help = "Draw tech tree"

    def add_arguments(self, parser):
        parser.add_argument("--buildDir", type=str, default="_build",
            help="Build directory" )
        # parser.add_argument("--sourceFile", type=str, help="Instead of downloading, read entities from file")
        # parser.add_argument("--cacheFile", type=str, help="After successful update, store entities to given file")
        pass

    def handle(self, *args, **kwargs):
        buildDir = kwargs["buildDir"]
        builder = tech.TechBuilder(buildDir)
        print("Building labels...", end="")
        builder.generateTechLabels()
        print(" Done")

        print("Building graph...", end="")
        builder.generateFullGraph()
        print(" Done")
        # techs = TechModel.objects.all()

        # tech.techNode(sys.stdout, techs[1])

        # dot.digraphHeader(sys.stdout)
        # for t in techs:
        #     tech.declareTech(sys.stdout, t, tech.fullLabel)
        # for t in techs:
        #     tech.declareTechEdges(sys.stdout, t)
        # dot.endGraph(sys.stdout)






