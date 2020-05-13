from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator

from .resource import ResourceModel
from .tech import TechModel
from .entity import EntityModel

class CreateModel(EntityModel):
    flavour = models.TextField()
    icon = models.CharField(max_length=30)
    tech = models.ForeignKey(TechModel, on_delete=models.CASCADE, related_name="tech")
    build = models.ForeignKey(TechModel, on_delete=models.CASCADE, related_name="build")
    result = models.ForeignKey(ResourceModel, on_delete=models.CASCADE)
    resultCount = models.IntegerField(validators=[MinValueValidator(0)])

class CreateInputModel(models.Model):
    parent = models.ForeignKey(CreateModel, on_delete=models.CASCADE)
    resource = models.ForeignKey(ResourceModel, on_delete=models.CASCADE)
    count = models.IntegerField(validators=[MinValueValidator(0)])
