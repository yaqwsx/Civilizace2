from django.core.management import BaseCommand
from core.models import User, Team

GROUPS = ["super", "org"]

def teamPlayers(name, password):
    return [{"username": f"{name}{i+1}", "password": password} for i in range(4)]

TEAMS = {
    "Černí": {
        "players": teamPlayers("cerny", "zlutevejce"),
        "id": "tym-cerni",
        "color": "gray-600"
    },
    "Červení": {
        "players": teamPlayers("cerveny", "modrypomeranc"),
        "id": "tym-cerveni",
        "color": "red-600"
    },
    "Oranžoví": {
        "players": teamPlayers("oranzovy", "hladkypapir"),
        "id": "tym-oranzovi",
        "color": "orange-500"
    },
    "Žlutí": {
        "players": teamPlayers("zluty", "kluzkystrom"),
        "id": "tym-zluti",
        "color": "yellow-500"
    },
    "Zelení": {
        "players": teamPlayers("zeleny", "pruhlednyhrnek"),
        "id": "tym-zeleni",
        "color": "green-600"
    },
    "Modří": {
        "players": teamPlayers("modry", "zelenaspona"),
        "id": "tym-modri",
        "color": "blue-600"
    },
    "Fialoví": {
        "players": teamPlayers("fialovy", "kvetoucistrom"),
        "id": "tym-fialovi",
        "color": "purple-500"
    },
    "Růžoví": {
        "players": teamPlayers("ruzovy", "nevyrovnanyuhel"),
        "id": "tym-ruzovi",
        "color": "pink-600"
    },
    "Protinožci": {
        "players": [{"username": "protinozec", "password": "zemekoule"}],
        "id": "tym-protinozci",
        "color": "white"
    }
}


SUPER_USERS = ["maara", "honza", "heno", "stouri", "system"]
ORG = ["jupi", "efka", "darwin", "martin", "zuzka", "maruska", "stouri",
       "liska", "tinka", "ivka", "tom", "timan", "zaloha"]

class Command(BaseCommand):
    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)

    help = "usage: create [entities|users|state]+"

    @staticmethod
    def create_or_get_user(username, password, superuser=False):
        try:
            return User.objects.get(username=username)
        except User.DoesNotExist:
            if superuser:
                return User.objects.create_superuser(username=username,
                                                     password=password)
            else:
                return User.objects.create_user(username=username,
                                                password=password)

    def add_arguments(self, parser):
        parser.add_argument('what', nargs='+', type=str)

    def handle(self, *args, **options):
        for what in options["what"]:
            if what == "entities":
                self.createEntities()
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
                if team.id == "tym-protinozci":
                    team.visible = False
                    team.save()
                print("Creating team: " + str(team))
            for userParams in teamParams["players"]:
                user = Command.create_or_get_user(
                        username=userParams["username"],
                        password=userParams["password"],)
        for username in ORG:
            user = Command.create_or_get_user(
                            username=username,
                            password="macatymaara",
                            superuser=False)
        for username in SUPER_USERS:
            user = Command.create_or_get_user(
                            username=username,
                            password="jogurt",
                            superuser=True)

    def createState(self):
        raise NotImplementedError("Not implemented yet")

    def createEntities(self):
        raise NotImplementedError("Not implemented yet")

