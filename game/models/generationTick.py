from django.db import models

class GenerationTick(models.Model):
    running = models.BooleanField(default=False)
    period = models.IntegerField(default=15 * 60)
    forceUpdate = models.BooleanField(default=False)