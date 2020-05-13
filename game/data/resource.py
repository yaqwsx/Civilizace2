from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator

from .entity import EntityModel

class ResourceTypeModel(EntityModel):
    color = models.CharField(max_length=7)

class ResourceModel(EntityModel):
    type = models.ForeignKey(ResourceTypeModel, on_delete=models.CASCADE, null=True)
    icon = models.CharField(max_length=30)
    level = models.IntegerField(validators=[MinValueValidator(2), MaxValueValidator(6)])
    isProduction = models.BooleanField(default=False)

