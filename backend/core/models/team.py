from django.db import models


class Team(models.Model):
    id = models.CharField(max_length=32, primary_key=True)
    name = models.CharField("Name", max_length=100, null=False)
    color = models.CharField("Color", max_length=20, null=False)
    visible = models.BooleanField(default=True)
