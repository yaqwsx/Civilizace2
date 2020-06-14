# https://stackoverflow.com/questions/22250352/programmatically-create-a-django-group-with-permissions

from django.core.management import BaseCommand
from django.contrib.auth.models import Group, Permission
from guardian.shortcuts import assign_perm

from game.models.actionMovesList import ActionMove
from game.models.users import User, Team
from game.models.state import State

from game.data.update import Update, UpdateError

GROUPS = ["super", "org"]

TEAMS = {
    "Červení": {
        "members": ["franta", "pavel"],
        "keyword": "JABLKO"
    },
    "Modří": {
        "members": ["eliska", "magda"],
        "keyword": "HRUSKA"
    },
    "Zelení": {
        "members": ["pepa", "vlada"],
        "keyword": "MANDARINKA"
    }
}

SUPER_USERS = ["maara", "honza"]
ORG = ["abbe", "jupi", "efka", "kaja", "domca"]

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
            try:
                # There can be more than one team with the name - do not use get
                team = Team.objects.all().filter(name=teamName).first()
                if not team:
                    raise RuntimeError()
            except:
                team = Team.objects.create(name=teamName)
                print("Creating team: " + str(team))
            for username in teamParams["members"]:
                user = Command.create_or_get_user(
                            username=username,
                            email=username + "@hrac.cz",
                            password="password")
                perm = Permission.objects.get(codename="stat_team")
                assign_perm(perm, user, team)
        org = Group.objects.get(name='org')
        for username in ORG:
            user = Command.create_or_get_user(
                            username=username,
                            email=username + "@org.cz",
                            password="password",
                            superuser=True)
            user.groups.add(org)
        superGroup = Group.objects.get(name='super')
        for username in SUPER_USERS:
            user = Command.create_or_get_user(
                            username=username,
                            email=username + "@super.cz",
                            password="password")
            user.groups.add(superGroup)

    def createGroups(self):
        for group_name in GROUPS:
            group, created = Group.objects.get_or_create(name=group_name)

    def createState(self):
        s = State.objects.createInitial()
        if s is None:
            print("Cannot create initialState")
        else:
            print("Initial state created: {}".format(s))

    def createEntities(self):
        updater = Update()
        updater.fileAsSource("game/data/entities.json")
        updater.update()