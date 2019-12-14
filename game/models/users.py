from django.db import models
from django.contrib.auth.models import AbstractUser
from guardian.shortcuts import get_objects_for_user

class Team(models.Model):
    name = models.CharField("Name", max_length=100, null=True)

    class Meta:
        permissions = (
            ("stat_team", "Can view stats for the team"),
            ("play_team", "Can play for the team"),
        )


class User(AbstractUser):
    def team(self):
        return get_objects_for_user(self, "game.stat_team").first()

    def isATeam(self):
        return self.groups.filter(name__in=["ATeam"])

    def isBTeam(self):
        return self.groups.filter(name__in=["BTeam"])

    def isOrg(self):
        return self.groups.filter(name__in=["ATeam", "BTeam"])

    def isPlayer(self):
        return not self.isOrg()