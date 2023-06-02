from django.core.management import BaseCommand, CommandError

from core.models.team import Team
from core.serializers.fields import enum_map
from game.models import DbEntities, StickerType
from game.stickers import makeSticker


class Command(BaseCommand):
    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)

    def add_arguments(self, parser):
        parser.add_argument("entity", type=str, help="Entity")
        parser.add_argument(
            "s_type",
            type=str.lower,
            choices=[name.lower() for name in StickerType._member_names_],
            help=f"Sticker type (choices: {', '.join(name.lower() for name in StickerType._member_names_)})",
            metavar="type",
        )
        parser.add_argument("team", type=str, help="Team")
        parser.add_argument("output", type=str, help="Output filepath")

    def handle(self, entity: str, s_type: str, team: str, output: str, *args, **kwargs):
        _, entities = DbEntities.objects.get_revision()
        if entity not in entities:
            raise CommandError(f"Entity {entity!r} doesn't exist")

        stickerType: StickerType = next(
            value
            for name, value in enum_map(StickerType).items()
            if name.lower() == s_type.lower()
        )

        try:
            teamModel = Team.objects.get(pk=team)
        except Team.DoesNotExist:
            raise CommandError(
                f"Team {team!r} doesn't exist - available teams are {[team.pk for team in  Team.objects.all()]}"
            )

        img = makeSticker(entities[entity], teamModel, stickerType)
        img.save(output)
        print(f"Height: {int(img.height / 180 * 25.4)}")
