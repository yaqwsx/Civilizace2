from django.db import models
from django.db.models.base import Model
from game.models.users import Team, User
from django_enumfield import enum

class MessageType(enum.Enum):
    normal = 1
    errata = 2
    announcement = 3

    __labels__ = {
        normal: "Běžné oznámení",
        errata: "Úprava pravidel",
        announcement: "Důležité oznámení"
    }

class Message(models.Model):
    author = models.ForeignKey("User", on_delete=models.PROTECT)
    appearDateTime = models.DateTimeField("Time of appearance the message")
    type = enum.EnumField(MessageType)
    content = models.TextField("Message content")

    def allowedTeams(self):
        return self.messagestatus_set.filter(visible=True)

    def isPublic(self):
        return self.allowedTeams().count() == Team.objects.count()

class MessageStatus(models.Model):
    team = models.ForeignKey(Team, on_delete=models.PROTECT)
    message = models.ForeignKey(Message, on_delete=models.CASCADE)
    visible = models.BooleanField()


class MessageRead(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.PROTECT)
