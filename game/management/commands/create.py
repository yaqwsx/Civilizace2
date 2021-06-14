# https://stackoverflow.com/questions/22250352/programmatically-create-a-django-group-with-permissions

from django.core.management import BaseCommand
from django.contrib.auth.models import Group, Permission
from guardian.shortcuts import assign_perm

from game.models.actionTypeList import ActionType
from game.models.users import User, Team
from game.models.state import State
from game.models.actionBase import ActionContext
from game.models.generationTick import GenerationTickSettings, ExpectedGeneration
from game.data.entity import EntitiesVersion

from game.data.update import Update, UpdateError

GROUPS = ["super", "org"]

TEAMS = {
    "Černí": {
        "players": [
            {
                "username": "cerny1",
                "password": "password",
            },
            {
                "username": "cerny2",
                "password": "password",
            }
        ],
        "id": "tym-cerni",
        "color": "gray-600"
    },
    "Červení": {
        "players": [],
        "id": "tym-cerveni",
        "color": "red-600"
    },
    "Oranžoví": {
        "players": [],
        "id": "tym-oranzovi",
        "color": "orange-500"
    },
    "Žlutí": {
        "players": [],
        "id": "tym-zluti",
        "color": "yellow-500"
    },
    "Zelení": {
        "players": [],
        "id": "tym-zeleni",
        "color": "green-600"
    },
    "Modří": {
        "players": [],
        "id": "tym-modri",
        "color": "blue-600"
    },
    "Fialoví": {
        "players": [],
        "id": "tym-fialovi",
        "color": "purple-500"
    },
    "Růžoví": {
        "players": [],
        "id": "tym-ruzovi",
        "color": "pink-600"
    }
}


SUPER_USERS = ["maara", "honza", "system"]
ORG = ["abbe", "jupi", "efka", "kaja", "darwin", "martin", "liska", "tinka", "ivka", "tom", "zaloha"]

class Command(BaseCommand):
    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)

    help = "usage: create [entities|groups|users|state]+"

    @staticmethod
    def create_or_get_user(username, email, password, superuser=False):
        try:
            return User.objects.get(username=username)
        except User.DoesNotExist:
            if superuser:
                return User.objects.create_superuser(username=username,
                    email=email, password=password)
            else:
                return User.objects.create_user(username=username, email=email,
                    password=password)

    def add_arguments(self, parser):
        parser.add_argument('what', nargs='+', type=str)


    def handle(self, *args, **options):
        for what in options["what"]:
            if what == "entities":
                self.createEntities()
            if what == "groups":
                self.createGroups()
            if what == "users":
                self.createUsers()
            if what == "state":
                self.createState()

    def createUsers(self):
        # Create team users
        for teamName, teamParams in TEAMS.items():
            # There can be more than one team with the name - do not use get
            team = Team.objects.all().filter(name=teamName).first()
            if not team:
                team = Team.objects.create(id=teamParams["id"], name=teamName,
                    color=teamParams["color"])
                print("Creating team: " + str(team))
            for userParams in teamParams["players"]:
                user = Command.create_or_get_user(
                        username=userParams["username"],
                        email=userParams["username"] + "@hrac.cz",
                        password=userParams["password"],)
                perm = Permission.objects.get(codename="stat_team")
                assign_perm(perm, user, team)
        org = Group.objects.get(name='org')
        for username in ORG:
            user = Command.create_or_get_user(
                            username=username,
                            email=username + "@org.cz",
                            password="macatymaara",
                            superuser=True)
            user.groups.add(org)
        superGroup = Group.objects.get(name='super')
        for username in SUPER_USERS:
            user = Command.create_or_get_user(
                            username=username,
                            email=username + "@super.cz",
                            password="jogurt")
            user.groups.add(superGroup)

    def createGroups(self):
        for group_name in GROUPS:
            group, created = Group.objects.get_or_create(name=group_name)

    def createState(self):
        context = ActionContext(EntitiesVersion.objects.getNewest())
        s = State.objects.createInitial(context)
        if s is None:
            print("Cannot create initialState")
        else:
            print("Initial state created: {}".format(s))

        ExpectedGeneration.objects.create()
        GenerationTickSettings.objects.create()

    def createEntities(self):
        updater = Update()
        updater.fileAsSource("game/data/entities.json")
        updater.update()