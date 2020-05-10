from django.core.validators import MinValueValidator
from django.db import models

from .resource import ResourceModel
from .entities import EntityModel, GameDataModel

class TechModel(EntityModel):
    culture = models.IntegerField(validators=[MinValueValidator(0)])
    flavour = models.TextField()
    task = models.TextField()
    notes = models.TextField()

class TechEdgeModel(EntityModel):
    srcTech = models.ForeignKey(TechModel, on_delete=models.CASCADE, related_name="src")
    dstTech = models.ForeignKey(TechModel, on_delete=models.CASCADE, related_name="dst")

class TechEdgeInputModel(EntityModel):
    parent = models.ForeignKey(TechEdgeModel, on_delete=models.CASCADE)
    resource = models.ForeignKey(ResourceModel, on_delete=models.CASCADE)
    count = models.IntegerField(validators=[MinValueValidator(0)])
