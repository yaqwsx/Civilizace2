from django.db import models
from game.models import Team

class Message(models.Model):
    author = models.ForeignKey("User", on_delete=models.PROTECT)
    appearDateTime = models.DateTimeField("Time of appearance the message")
    content = models.TextField("Message content")

class MessageStatus(models.Model):
    team = models.ForeignKey(Team, on_delete=models.PROTECT)
    message = models.ForeignKey(Message, on_delete=models.CASCADE)
    visible = models.BooleanField()
    read = models.BooleanField(default=False)
