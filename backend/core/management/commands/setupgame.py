import os
import json
from argparse import ArgumentParser
from typing import Optional
from django.core.management import BaseCommand
from frozendict import frozendict
from game.entities import Entities, Entity, EntityId, Org, OrgRole, Team as TeamEntity
from game.entityParser import EntityParser
from django.conf import settings
from game.models import DbAction, DbDelayedEffect, DbEntities, DbInteraction, DbSticker, DbTick, DbTurn, DbState, DbTeamState, DbMapState
from core.models.announcement import Announcement
from core.models import User, Team as DbTeam
from game.state import GameState
from django.db import transaction

from game.viewsets.action import ActionViewSet

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
        parser.add_argument("entities", type=str)

    def handle(self, entities: str, *args, **options) -> None:
        targetFile = settings.ENTITY_PATH / setFilename(entities)
        ent = EntityParser.load(targetFile)

        with transaction.atomic():
            self.clearGame()

            self.createOrgs(ent.orgs)
            self.createTeams(ent.teams)
            self.createEntities(targetFile)
            self.createInitialState(ent, entities)
            self.createRounds()

    def clearGame(self) -> None:
        DbTick.objects.all().delete()
        DbSticker.objects.all().delete()
        DbDelayedEffect.objects.all().delete()
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
            assert org.password is not None, 'Org cannot have a blank password'
            self.create_or_update_user(username = org.id[4:], password=org.password,
                                          superuser=org.role == OrgRole.SUPER)

    def createTeams(self, teams: frozendict[EntityId, TeamEntity]) -> None:
        for team in teams.values():
            teamModel = DbTeam.objects.create(id=team.id,
                                                 name=team.name,
                                                 color=team.color,
                                                 visible=team.visible,
                                                 )
            for i in range(4):
                assert team.password is not None, 'Team cannot have a blank password'
                self.create_or_update_user(username=f"{team.id[4:]}{i+1}",
                    password=team.password, superuser=False, team=teamModel)

    def createEntities(self, entityFile: str | os.PathLike[str]) -> None:
        with open(entityFile) as f:
            data = json.load(f)
        DbEntities.objects.create(data=data)

    def createInitialState(self, entities: Entities, setname: str) -> None:
        if setname == "TEST":
            from game.tests.actions.common import createTestInitState
            irState = createTestInitState()
        else:
            irState = GameState.createInitial(entities)
        state = DbState.objects.createFromIr(irState)
        stickers = {t: s.collectStickerEntitySet() for t, s in irState.teamStates.items()}
        res = set()
        for t, sSet in stickers.items():
            for e in sSet:
                res.add((t, e))
        ActionViewSet._awardStickers(res)


    def createRounds(self) -> None:
        for i in range(200):
            DbTurn.objects.create(duration=15 * 60 if os.environ.get("CIV_SPEED_RUN", None) != "1" else 60)

