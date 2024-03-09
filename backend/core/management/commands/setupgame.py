import json
import os
from argparse import ArgumentParser
from typing import Optional

from django.conf import settings
from django.core.management import BaseCommand
from django.db import transaction
from frozendict import frozendict
from typing_extensions import override

from core.models import Team, User
from core.models.announcement import Announcement
from game.entities import Entities, EntityId, OrgEntity, OrgRole, TeamEntity
from game.entityParser import EntityParser
from game.models import (
    DbAction,
    DbEntities,
    DbInteraction,
    DbMapState,
    DbScheduledAction,
    DbState,
    DbSticker,
    DbTeamState,
    DbTurn,
)
from game.state import GameState, WorldState
from game.viewsets.action_view_helper import ActionViewHelper
from game.viewsets.stickers import Sticker

from .pullentities import ENTITY_SETS, setFilename


class Command(BaseCommand):
    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)

    help = "usage: create [entities|users|state]+"

    @override
    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument("set", type=str, choices=list(ENTITY_SETS), help="Entities set")

    @override
    def handle(self, set: str, *args, **options) -> None:
        assert set in ENTITY_SETS
        targetFile = settings.ENTITY_PATH / setFilename(set)
        entities = EntityParser.load(targetFile)

        with transaction.atomic():
            self.clear_game()

            self.create_orgs(entities.orgs)
            self.create_teams(entities.teams)
            self.create_entities(targetFile)
            self.create_initial_state(entities)
            self.create_rounds()

    @staticmethod
    def clear_game() -> None:
        DbSticker.objects.all().delete()
        DbScheduledAction.objects.all().delete()
        DbEntities.objects.all().delete()
        DbAction.objects.all().delete()
        DbInteraction.objects.all().delete()
        DbTeamState.objects.all().delete()
        DbState.objects.all().delete()
        DbTurn.objects.all().delete()
        DbMapState.objects.all().delete()

        Announcement.objects.all().delete()
        User.objects.all().delete()
        Team.objects.all().delete()

    @staticmethod
    def create_orgs(orgs: frozendict[EntityId, OrgEntity]) -> None:
        for org in orgs.values():
            assert org.username, f"Org {org} cannot have a blank username"
            assert org.password, f"Org {org} cannot have a blank password"
            User.update_or_create(
                username=org.username,
                password=org.password,
                superuser=org.role == OrgRole.SUPER,
            )

    @staticmethod
    def create_teams(teams: frozendict[EntityId, TeamEntity]) -> None:
        for team in teams.values():
            teamModel = Team.objects.create(
                id=team.id,
                name=team.name,
                color=team.color,
                visible=team.visible,
            )
            for i in range(4):
                assert team.username, f"Team {team} cannot have a blank username"
                assert team.password, f"Team {team} cannot have a blank password"
                User.update_or_create(
                    username=f"{team.id[4:]}{i+1}",
                    password=team.password,
                    superuser=False,
                    team=teamModel,
                )

    @staticmethod
    def create_entities(entityFilename: str | os.PathLike[str]) -> None:
        with open(entityFilename) as f:
            data = json.load(f)
        DbEntities.objects.create(data=data)

    @staticmethod
    def create_initial_state(entities: Entities) -> None:
        irState = GameState.create_initial(entities)
        DbState.objects.create_from(irState, source=None)
        stickers = {
            t: s.collectStickerEntitySet() for t, s in irState.teamStates.items()
        }
        res = set()
        for t, sSet in stickers.items():
            for e in sSet:
                res.add(Sticker(t, e))
        ActionViewHelper._awardStickers(res)

    @staticmethod
    def create_rounds() -> None:
        for i in range(200):
            DbTurn.objects.create(
                duration=15 * 60 if os.environ.get("CIV_SPEED_RUN", None) != "1" else 60
            )
