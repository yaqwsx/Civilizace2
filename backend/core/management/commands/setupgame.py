import os
import json
from argparse import ArgumentParser
from typing import Optional
from django.core.management import BaseCommand
from frozendict import frozendict
from game.entities import Entities, EntityId, Org, OrgRole, Team as TeamEntity
from game.entityParser import EntityParser
from django.conf import settings
from game.models import DbAction, DbEntities, DbInteraction, DbScheduledAction, DbSticker, DbTick, DbTurn, DbState, DbTeamState, DbMapState
from core.models.announcement import Announcement
from core.models import User, Team as DbTeam
from game.state import GameState, WorldState
from django.db import transaction

from game.viewsets.action_view_helper import ActionViewHelper
from game.viewsets.stickers import Sticker

from .pullentities import setFilename

class Command(BaseCommand):
    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)

    help = "usage: create [entities|users|state]+"

    @staticmethod
    def create_or_update_user(username: str, password: str, *, superuser: bool=False, team: Optional[DbTeam]=None) -> User:
        assert password is not None
        assert not superuser or team is None
        try:
            user: User = User.objects.get(username=username)
            user.set_password(password)
            user.team = team
            user.is_superuser = superuser
            user.save()
            return user
        except User.DoesNotExist:
            if superuser:
                return User.objects.create_superuser(username=username,
                                                     password=password)
            else:
                return User.objects.create_user(username=username,
                                                password=password,
                                                team=team)

    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument("set", type=str)

    def handle(self, set: str, *args, **options) -> None:
        targetFile = settings.ENTITY_PATH / setFilename(set)
        data = EntityParser.load(targetFile)

        with transaction.atomic():
            self.clearGame()

            self.createOrgs(data.entities.orgs)
            self.createTeams(data.entities.teams)
            self.createEntities(targetFile)
            self.createInitialState(data.entities, data.init_world_state)
            self.createRounds()

    def clearGame(self) -> None:
        DbTick.objects.all().delete()
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
        DbTeam.objects.all().delete()

    def createOrgs(self, orgs: frozendict[EntityId, Org]) -> None:
        for org in orgs.values():
            assert org.username is not None, f'Org {org} cannot have a blank username'
            assert org.password is not None, f'Org {org} cannot have a blank password'
            self.create_or_update_user(username = org.username, password=org.password,
                                          superuser=org.role == OrgRole.SUPER)

    def createTeams(self, teams: frozendict[EntityId, TeamEntity]) -> None:
        for team in teams.values():
            teamModel = DbTeam.objects.create(id=team.id,
                                                 name=team.name,
                                                 color=team.color,
                                                 visible=team.visible,
                                                 )
            for i in range(4):
                assert team.username is not None, f'Team {team} cannot have a blank username'
                assert team.password is not None, f'Team {team} cannot have a blank password'
                self.create_or_update_user(username=f"{team.id[4:]}{i+1}",
                    password=team.password, superuser=False, team=teamModel)

    def createEntities(self, entityFilename: str | os.PathLike[str]) -> None:
        with open(entityFilename) as f:
            data = json.load(f)
        DbEntities.objects.create(data=data)

    def createInitialState(self, entities: Entities, initWorldState: WorldState) -> None:
        irState = GameState.createInitial(entities, initWorldState)
        state = DbState.objects.createFromIr(irState)
        stickers = {t: s.collectStickerEntitySet() for t, s in irState.teamStates.items()}
        res = set()
        for t, sSet in stickers.items():
            for e in sSet:
                res.add(Sticker(t, e))
        ActionViewHelper._awardStickers(res)


    def createRounds(self) -> None:
        for i in range(200):
            DbTurn.objects.create(duration=15 * 60 if os.environ.get("CIV_SPEED_RUN", None) != "1" else 60)

