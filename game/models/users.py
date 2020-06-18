from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models import Count, Q
from guardian.shortcuts import get_objects_for_user

from game.models.actionBase import Action, ActionPhase


class Team(models.Model):
    name = models.CharField("Name", max_length=100, null=False)
    color = models.CharField("Color", max_length=20, null=False)

    def unfinishedAction(self):
        """ Return an action for the team which is initiated but not committed, abandoned or canceled """
        unfinished = Action.objects \
            .filter(actionstep__action__team=self.id) \
            .annotate(
                initcount=Count('actionstep',
                    filter=Q(actionstep__phase=ActionPhase.initiate))) \
            .annotate(allcount=Count('actionstep')) \
            .filter(initcount=1, allcount=1)[:1]
        if unfinished:
            return unfinished[0].resolve()
        return None

    class Meta:
        permissions = (
            ("stat_team", "Can view stats for the team"),
            ("play_team", "Can play for the team"),
        )


class User(AbstractUser):
    def team(self):
        return get_objects_for_user(self, "game.stat_team").first()

    def isOrg(self):
        return self.groups.filter(name__in=["org", "super"])

    def isSuperUser(self):
        return self.groups.filter(name="super")

    def isPlayer(self):
        return not self.isOrg()

    def isInGroup(self, groupName):
        for group in self.groups.all():
            if groupName in group:
                return True
        return False