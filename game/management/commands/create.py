# https://stackoverflow.com/questions/22250352/programmatically-create-a-django-group-with-permissions

from django.core.management import BaseCommand
from django.contrib.auth.models import User, Group, Permission
from guardian.shortcuts import assign_perm
from game import models

GROUPS_PERMISSIONS = {
    'ATeam': {
        models.Team: ['play', 'stat']
    },
    'BTeam': {
        models.Team: ['play', 'stat']
    },
}

TEAMS = {
    "Červení": {
        "members": ["franta", "pavel"]
    },
    "Modří": {
        "members": ["eliska", "magda"]
    },
    "Zelení": {
        "members": ["pepa", "vlada"]
    }
}

ATEAM = ["maara", "honza", "abbe", "jupi", "efka"]
BTEAM = ["kaja", "domca"]

class Command(BaseCommand):
    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)

    help = "usage: create [groups|users|state]+"

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
            if what == "groups":
                self.createGroups()
            if what == "users":
                self.createUsers()
            if what == "state":
                self.createState()

    def createUsers(self):
        # Create team users
        for teamName, teamParams in TEAMS.items():
            team = models.Team(name=teamName)
            team.save()
            for username in teamParams["members"]:
                user = Command.create_or_get_user(
                            username=username,
                            email=username + "@hrac.cz",
                            password="password")
                assign_perm("stat_team", user, team)
        ateamGroup = Group.objects.get(name='ATeam')
        for username in ATEAM:
            user = Command.create_or_get_user(
                            username=username,
                            email=username + "@ateam.cz",
                            password="password",
                            superuser=True)
            user.groups.add(ateamGroup)
        bteamGroup = Group.objects.get(name='BTeam')
        for username in BTEAM:
            user = Command.create_or_get_user(
                            username=username,
                            email=username + "@bteam.cz",
                            password="password")
            user.groups.add(bteamGroup)

    def createGroups(self):
        for group_name in GROUPS_PERMISSIONS:
            group, created = Group.objects.get_or_create(name=group_name)
            for model_cls in GROUPS_PERMISSIONS[group_name]:
                for perm_index, perm_name in \
                        enumerate(GROUPS_PERMISSIONS[group_name][model_cls]):

                    # Generate permission name as Django would generate it
                    codename = perm_name + "_" + model_cls._meta.model_name
                    try:
                        # Find permission object and add to group
                        perm = Permission.objects.get(codename=codename)
                        group.permissions.add(perm)
                        self.stdout.write("Adding "
                                          + codename
                                          + " to group "
                                          + group.__str__())
                    except Permission.DoesNotExist:
                        self.stdout.write(codename + " not found")

    def createState(self):
        s = models.State.objects.createInitial()
        if s is None:
            print("Cannot create initialState")
        else:
            print("Initial state created: {}".format(s))