from typing import Dict
import json
from typing import List
from django.core.management import BaseCommand
from game.entities import Entity, EntityId, Org, OrgRole, Team as TeamEntity
from game.entityParser import loadEntities
from django.conf import settings
from game.models import DbAction, DbEntities, DbInteraction, DbState, DbTeamState, DbWorldState
from core.models import User, Team

from .pullentities import setFilename

class Command(BaseCommand):
    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)

    help = "usage: create [entities|users|state]+"

    @staticmethod
    def create_or_update_user(username, password, superuser=False, team=None):
        try:
            u = User.objects.get(username=username)
            u.set_password(password)
            u.team = team
            u.is_superuser = superuser
            u.save()
            return u
        except User.DoesNotExist:
            if superuser:
                return User.objects.create_superuser(username=username,
                                                     password=password)
            else:
                return User.objects.create_user(username=username,
                                                password=password,
                                                team=team)

    def add_arguments(self, parser):
        parser.add_argument("entities", type=str)

    def handle(self, entities, *args, **options):
        targetFile = settings.ENTITY_PATH / setFilename(entities)
        ent = loadEntities(targetFile)

        self.clearGame()

        self.createOrgs(ent.orgs)
        self.createTeams(ent.teams)
        self.createEntities(targetFile)

    def clearGame(self):
        User.objects.all().delete()
        Team.objects.all().delete()
        DbEntities.objects.all().delete()
        DbAction.objects.all().delete()
        DbInteraction.objects.all().delete()
        DbTeamState.objects.all().delete()
        DbWorldState.objects.all().delete()
        DbState.objects.all().delete()

    def createOrgs(self, orgs: Dict[EntityId, Org]) -> None:
        for o in orgs.values():
            self.create_or_update_user(username = o.id[4:], password=o.password,
                                          superuser=o.role == OrgRole.SUPER)

    def createTeams(self, teams: Dict[EntityId, TeamEntity]) -> None:
        for t in teams.values():
            teamModel = Team.objects.create(id=t.id, name=t.name, color=t.color,
                                            visible=t.visible)
            for i in range(4):
                self.create_or_update_user(username=f"{t.id[4:]}{i+1}",
                    password=t.password, superuser=False, team=teamModel)

    def createEntities(self, entityFile) -> None:
        with open(entityFile) as f:
            data = json.load(f)
        DbEntities.objects.create(data=data)

