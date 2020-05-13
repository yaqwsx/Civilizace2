from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator

from .resource import ResourceModel
from .tech import TechModel
from .entity import EntityModel, DieModel

class VyrobaModel(EntityModel):
    flavour = models.TextField()
    tech = models.ForeignKey(TechModel, on_delete=models.CASCADE, related_name="tech")
    build = models.ForeignKey(TechModel, on_delete=models.CASCADE, related_name="build", null=True)
    result = models.ForeignKey(ResourceModel, on_delete=models.CASCADE)
    amount = models.IntegerField(validators=[MinValueValidator(0)])
    die = models.ForeignKey(DieModel, on_delete=models.CASCADE)
    dots = models.IntegerField()


class VyrobaInputModel(models.Model):
    parent = models.ForeignKey(VyrobaModel, on_delete=models.CASCADE)
    resource = models.ForeignKey(ResourceModel, on_delete=models.CASCADE)
    amount = models.IntegerField(validators=[MinValueValidator(0)])
