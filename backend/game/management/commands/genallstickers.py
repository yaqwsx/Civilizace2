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

        for t in entities.techs.values():
            for stickerType in [
                StickerType.regular,
                StickerType.techSmall,
                StickerType.techFirst,
            ]:
                img = makeSticker(t, Team.objects.get(pk="tym-zeleni"), stickerType)
                img.save(str(outputdir / f"{t.id}-{stickerType}.png"))
        for v in entities.vyrobas.values():
            img = makeSticker(v, Team.objects.get(pk="tym-zeleni"), StickerType.regular)
            img.save(str(outputdir / f"{v.id}.png"))
        for b in entities.buildings.values():
            img = makeSticker(b, Team.objects.get(pk="tym-zeleni"), StickerType.regular)
            img.save(str(outputdir / f"{b.id}.png"))
