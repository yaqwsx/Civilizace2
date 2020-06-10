from django.core.management import BaseCommand

from game.data.icons import downloadIcons

class Command(BaseCommand):
    help = "Download graphics"
    defaultFile = "game/data/entities.json"

    def add_arguments(self, parser):
        parser.add_argument("--directory", type=str, required=False,
            help="Instead of downloading, read entities from file")

    def handle(self, *args, **kwargs):
        directory = kwargs.get("--directory", "game/static/icons")
        downloadIcons(directory)



