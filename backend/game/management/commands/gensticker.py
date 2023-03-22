from django.core.management import BaseCommand
from core.models.team import Team as DbTeam
from game.models import DbEntities, StickerType



from game.stickers import makeSticker

class Command(BaseCommand):
    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)

    def add_arguments(self, parser):
        parser.add_argument("entity", type=str)
        parser.add_argument("type", type=str)
        parser.add_argument("team", type=str)
        parser.add_argument("output", type=str)

    def handle(self, entity, type, team, output, *args, **kwargs):
        _, entities = DbEntities.objects.get_revision()

        teamModel = DbTeam.objects.get(pk=team)

        stickerType = {
            "regular": StickerType.regular,
            "techsmall": StickerType.techSmall,
            "techfirst": StickerType.techFirst
        }[type.lower()]

        img = makeSticker(entities[entity], teamModel, stickerType)
        img.save(output)
        print(f"Height: {int(img.height / 180 * 25.4)}")



