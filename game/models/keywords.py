from django_enumfield import enum
from django.db import models

class KeywordType(enum.Enum):
    team = 0
    move = 1

class Keyword(models.Model):
    word = models.CharField("Game Word", max_length=30)
    description = models.CharField(max_length=150)
    valueType = enum.EnumField(KeywordType)
    value = models.IntegerField()