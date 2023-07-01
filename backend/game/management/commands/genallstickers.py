from django.core.management import BaseCommand
from core.models.team import Team
from game.entities import Building, BuildingUpgrade, Vyroba
from game.models import DbEntities, StickerType
from pathlib import Path


from game.stickers import makeSticker


class Command(BaseCommand):
    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)

    def add_arguments(self, parser):
        try:
            _, entities = DbEntities.objects.get_revision()
        except DbEntities.DoesNotExist:
            raise RuntimeError("Entities not loaded, try reseting the game")

        parser.add_argument("outputdir", type=str)
        parser.add_argument(
            "-t",
            "--team",
            choices=[t.id for t in entities.teams.values()],
            default=entities.teams.value(0).id,
        )

    def handle(self, outputdir, team, *args, **kwargs):
        outputdir = Path(outputdir)
        outputdir.mkdir(exist_ok=True, parents=True)
        try:
            _, entities = DbEntities.objects.get_revision()
        except DbEntities.DoesNotExist:
            raise RuntimeError("Entities not loaded, try reseting the game")

        dbTeam = Team.objects.get(id=team)

        for t in entities.techs.values():
            for stickerType in [
                StickerType.regular,
                StickerType.techSmall,
                StickerType.techFirst,
            ]:
                img = makeSticker(t, dbTeam, stickerType, entities=entities)
                img.save(str(outputdir / f"{t.id}-{stickerType}.png"))
        for e in entities.values():
            if isinstance(e, (Vyroba, Building, BuildingUpgrade)):
                img = makeSticker(e, dbTeam, StickerType.regular, entities=entities)
                img.save(str(outputdir / f"{e.id}.png"))
