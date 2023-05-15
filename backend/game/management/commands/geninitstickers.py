from django.core.management import BaseCommand
from core.models.team import Team
from game.models import DbEntities, StickerType
from pathlib import Path


from game.stickers import makeSticker


class Command(BaseCommand):
    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)

    def add_arguments(self, parser):
        parser.add_argument("outputdir", type=str)

    def handle(self, outputdir, *args, **kwargs):
        outputdir = Path(outputdir)
        outputdir.mkdir(exist_ok=True, parents=True)
        _, entities = DbEntities.objects.get_revision()

        stickers = [
            "vyr-drevoInit",
            "bui-centrum",
            "tec-start",
            "tec-plane",
            "tec-lesy",
            "tec-hory",
        ]

        for team in Team.objects.all():
            for s in stickers:
                img = makeSticker(entities[s], team, StickerType.regular)
                img.save(str(outputdir / f"{team.id}_{s}.png"))
