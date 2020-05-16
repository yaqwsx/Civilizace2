from django.core.validators import MinValueValidator
from django.db import models

from .resource import ResourceModel
from .entity import EntityModel, GameDataModel, DieModel

class TaskModel(EntityModel):
    text = models.TextField()

class TechModel(EntityModel):
    culture = models.IntegerField(validators=[MinValueValidator(0)], default=0)
    flavour = models.TextField()
    task = models.ForeignKey(TaskModel, on_delete=models.CASCADE)
    notes = models.TextField()
    image = models.TextField()
    nodeTag = models.TextField()

class TechEdgeModel(EntityModel):
    src = models.ForeignKey(TechModel, on_delete=models.CASCADE, related_name="unlocks_tech")
    dst = models.ForeignKey(TechModel, on_delete=models.CASCADE, related_name="unlocked_by")
    die = models.ForeignKey(DieModel, on_delete=models.CASCADE)
    dots = models.IntegerField()

class TechEdgeInputModel(models.Model):
    parent = models.ForeignKey(TechEdgeModel, on_delete=models.CASCADE, related_name="resources")
    resource = models.ForeignKey(ResourceModel, on_delete=models.CASCADE)
    amount = models.IntegerField(validators=[MinValueValidator(0)])

