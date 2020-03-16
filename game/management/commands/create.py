# https://stackoverflow.com/questions/22250352/programmatically-create-a-django-group-with-permissions

from django.core.management import BaseCommand
from django.contrib.auth.models import Group, Permission
from guardian.shortcuts import assign_perm
from game import models
from game.models import User
from game.models.keywords import KeywordType, Keyword

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

ATEAM = ["maara", "honza", "abbe", "jupi", "efka"]
BTEAM = ["kaja", "domca"]

KEYWORDS = [
    # keyword, description, category, value
    ("PETRZEL", "Zvyš počítadlo", KeywordType.move,
        models.ActionMove.sanboxIncreaseCounter)
]

class Command(BaseCommand):
    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)

    help = "usage: create [groups|users|state|keywords]+"

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
            if what == "keywords":
                self.createKeywords()

    def createUsers(self):
        # Create team users
        for teamName, teamParams in TEAMS.items():
            try:
                # There can be more than one team with the name - do not use get
                team = models.Team.objects.all().filter(name=teamName).first()
                if not team:
                    raise RuntimeError()
            except:
                team = models.Team.objects.create(name=teamName)
                print("Creating team: " + str(team))
            for username in teamParams["members"]:
                user = Command.create_or_get_user(
                            username=username,
                            email=username + "@hrac.cz",
                            password="password")
                perm = Permission.objects.get(codename="stat_team")
                assign_perm(perm, user, team)
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

    def createOrUpdateKeyword(self, keyword):
        try:
            k = Keyword.objects.get(word=keyword[0])
            k.word = keyword[0]
            k.description = keyword[1]
            k.valueType = keyword[2]
            k.value = keyword[3]
            k.save()
        except Keyword.DoesNotExist:
            Keyword.objects.create(word=keyword[0], description=keyword[1],
                valueType=keyword[2], value=keyword[3])

    def createKeywords(self):
        for keyword in KEYWORDS:
            self.createOrUpdateKeyword(keyword)
        for teamname, param in TEAMS.items():
            team = models.Team.objects.get(name=teamname)
            self.createOrUpdateKeyword((
                param["keyword"],
                "Play team " + teamname,
                KeywordType.team,
                team.id))
