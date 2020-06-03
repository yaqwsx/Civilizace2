from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator

from .entity import EntityModel

class ResourceTypeModel(EntityModel):
    color = models.CharField(max_length=7)

class ResourceModel(EntityModel):
    type = models.ForeignKey(ResourceTypeModel, on_delete=models.CASCADE, null=True)
    icon = models.CharField(max_length=30)
    level = models.IntegerField(validators=[MinValueValidator(2), MaxValueValidator(6)])

    @property
    def isGeneric(self):
        chunks = self.id.split("-")
        if chunks[0] not in ["mat", "prod"]: return False
        return len(chunks) > 2

    @property
    def isProduction(self):
        chunks = self.id.split("-")
        return chunks[0] == "prod"

