from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator

from .entity import EntityModel

class ResourceTypeModel(EntityModel):
    color = models.CharField(max_length=7)

class ResourceManager(models.Manager):
    def concreteResources(self, metaResource):
        assert(metaResource.isMeta)
        # Use all instead of filter as it have been probably already fetched...
        return [x for x in self.all() if x.isSpecializationOf(metaResource)]

class ResourceModel(EntityModel):
    type = models.ForeignKey(ResourceTypeModel, on_delete=models.CASCADE, null=True)
    icon = models.CharField(max_length=30)
    level = models.IntegerField(validators=[MinValueValidator(2), MaxValueValidator(6)])

    objects = ResourceManager()

    def concreteResources(self):
        if self.isMeta:
            return ResourceModel.objects.concreteResources(self)
        return [self]

    def isSpecializationOf(self, meta):
        if meta.isMeta:
            return (self.level >= meta.level and self.type == meta.type and
               not self.isMeta and meta.isProduction == self.isProduction)
        return self.id == meta.id

    @property
    def isMeta(self):
        chunks = self.id.split("-")
        if chunks[0] not in ["mat", "prod"]: return False
        return len(chunks) > 2

    @property
    def isProduction(self):
        chunks = self.id.split("-")
        return chunks[0] == "prod"

    @property
    def plainLabel(self):
        return self.label.replace("Produkce: ", "")

    def htmlRepr(self):
        if self.isProduction:
            name = f'<b>{self.plainLabel}</b>'
        else:
            name = self.label
        if self.icon:
            return f'<img class="inline-block" style="width: 30px; height: 30px" src="/static/icons/{self.icon}"><span class="text-gray-500">({name})</span>'
        return self.name

