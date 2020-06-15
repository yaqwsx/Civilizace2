from django.core.management import BaseCommand

from game.data.vyroba import VyrobaModel


class Command(BaseCommand):
    help = "Update entities"

    def add_arguments(self, parser):
        parser.add_argument("-f", type=str, required=False,
            help="Filter only vyrobas containing the specified string in id/label")

    def handle(self, *args, **kwargs):

        for vyroba in VyrobaModel.objects.all():
            if not vyroba.output.isProduction:
                continue

            relevant = False
            if not kwargs["f"]: relevant = True
            if (kwargs["f"] in vyroba.id or kwargs["f"] in vyroba.label): relevant = True
            if kwargs["f"] in vyroba.output.id or kwargs["f"] in vyroba.output.label: relevant = True

            if not relevant:
                continue

            print()
            print(f"{vyroba.id} : {vyroba.label}")
            print(f"   {vyroba.amount}x {vyroba.output.label}")
            
            for enhancer in vyroba.enhancers.all():
                print(f"  +{enhancer.amount}x : {enhancer.label}  {enhancer.tech.label} ({enhancer.tech.epocha})")
