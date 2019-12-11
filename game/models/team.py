from django.db import models

class Team(models.Model):
    name = models.CharField("Name", max_length=100, null=True)