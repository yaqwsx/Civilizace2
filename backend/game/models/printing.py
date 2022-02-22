from django.db import models
from django.utils import timezone
from datetime import timedelta

class PrinterManager(models.Manager):
    def prune(self):
        """
        Remove dead printers from database. Printer is considered dead after 1
        minute of inactivity.
        """
        criticalPoint = timezone.now() - timedelta(minutes=1)
        self.filter(registeredAt__lte=criticalPoint).delete()

class Printer(models.Model):
    name = models.CharField(max_length=200)
    address = models.CharField(max_length=200)
    port = models.IntegerField()
    registeredAt = models.DateTimeField()

    objects = PrinterManager()
