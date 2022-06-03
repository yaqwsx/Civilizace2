from django.db import models
from core.models.user import User
from core.models.team import Team
from django.db.models import Q
from django.utils import timezone

class AnnouncementType(models.IntegerChoices):
    normal = 1
    important = 2
    game = 3

class AnnouncementManager(models.Manager):
    def getUnread(self, user):
        return self.getTeam(user.team) \
            .filter(~models.Exists(
                ReadEvent.objects.filter(user=user, announcement=models.OuterRef("pk"))))

    def getTeamUnread(self, team):
        return self.getTeam(team) \
            .filter(~models.Exists(
                ReadEvent.objects.filter(announcement=models.OuterRef("pk"), user__team=team)
            ))

    def getTeam(self, team):
        return self.getVisible().filter(teams=team).prefetch_related("readevent_set")

    def getVisible(self):
        return self.get_queryset() \
            .filter(appearDatetime__lte=timezone.now()) \
            .order_by("-appearDatetime")

class Announcement(models.Model):
    author = models.ForeignKey(User, on_delete=models.PROTECT, related_name="announcementsFrom", null=True)
    appearDatetime = models.DateTimeField("Time of appearance the message")
    type = models.IntegerField(choices=AnnouncementType.choices, default=AnnouncementType.normal)
    content = models.TextField("Message content")
    teams = models.ManyToManyField(Team)
    read = models.ManyToManyField(User, through="ReadEvent")

    objects = AnnouncementManager()

    def typeString(self):
        return {
            1: "normal",
            2: "important",
            3: "game"
        }[self.type]

    def allowedTeams(self):
        return self.teamStatuses.filter(visible=True)

    def isPublic(self):
        return self.allowedTeams().count() == Team.objects.count()

    def seenByTeamAt(self, team):
        try:
            return ReadEvent.objects \
                .filter(announcement=self, user__team=team, readAt__isnull=False) \
                .order_by("readAt").first().readAt
        except ReadEvent.DoesNotExist:
            return None


class ReadEvent(models.Model):
    announcement = models.ForeignKey(Announcement, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    readAt = models.DateTimeField(auto_now=True)
