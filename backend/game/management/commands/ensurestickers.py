from django.core.management import BaseCommand
from core.models.team import Team
from game.models import DbEntities, DbState, DbSticker, StickerType
from pathlib import Path



from game.state import PlagueStats
from game.stickers import makeSticker, underline

class Command(BaseCommand):
    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)

    def handle(self, *args, **kwargs):
        revision, entities = DbEntities.objects.get_revision()
        dbState = DbState.objects.latest()
        state = dbState.toIr()
        stickers = {t: s.collectStickerEntitySet() for t, s in state.teamStates.items()}
        for t, stickers in stickers.items():
            for sticker in stickers:
                print(f"{t.id} - {sticker.id}")
                DbSticker.objects.update_or_create(
                    team=Team.objects.get(pk=t.id),
                    entityId=sticker.id,
                    type=StickerType.regular,
                    defaults={"entityRevision": revision})



