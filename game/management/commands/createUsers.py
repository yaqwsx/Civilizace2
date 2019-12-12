from django.core.management import BaseCommand
from django.contrib.auth.models import User, Group
from guardian.shortcuts import assign_perm
from game import models

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

    help = "Create test users"
    def handle(self, *args, **options):
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

