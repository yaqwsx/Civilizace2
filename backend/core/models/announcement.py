from django.db import models
from core.models.user import User
from core.models.team import Team

class AnnouncementType(models.IntegerChoices):
    normal = 1
    important = 2

class Announcement(models.Model):
    author = models.ForeignKey(User, on_delete=models.PROTECT, related_name="announcementsFrom", null=True)
    appearDatetime = models.DateTimeField("Time of appearance the message")
    type = models.IntegerField(choices=AnnouncementType.choices, default=AnnouncementType.normal)
    content = models.TextField("Message content")
    teams = models.ManyToManyField(Team)
    read = models.ManyToManyField(User)

    def allowedTeams(self):
        return self.teamStatuses.filter(visible=True)

    def isPublic(self):
        return self.allowedTeams().count() == Team.objects.count()

