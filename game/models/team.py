from django.db import models

class Team(models.Model):
    name = models.CharField("Name", max_length=100, null=True)

    class Meta:
        permissions = (
            ("stat_team", "Can view stats for the team"),
            ("play_team", "Can play for the team"),
        )