from django.core.validators import MinValueValidator
from django.db import models

from .resource import ResourceModel
from .entity import EntityModel, DieModel, IslandModel


class TechModel(EntityModel):
    culture = models.IntegerField(validators=[MinValueValidator(0)], default=0)
    flavour = models.TextField()
    notes = models.TextField()
    image = models.TextField()
    nodeTag = models.TextField()
    epocha = models.IntegerField()
    island = models.ForeignKey(IslandModel, null=True, on_delete=models.CASCADE,
        default=None, related_name="techs")
    defenseBonus = models.IntegerField()

    @property
    def isBuilding(self):
        return self.id.startswith("build-")

    def htmlRepr(self):
        return self.label

    def getAvailableTasks(self, team):
        """
        Return a list of all tasks that are available for this technology and
        have not been completed by the team yet.
        """
        raise NotImplementedError("Tell Honza to implement this. He was lazy at the moment")

class TechEdgeModel(EntityModel):
    src = models.ForeignKey(TechModel, on_delete=models.CASCADE, related_name="unlocks_tech")
    dst = models.ForeignKey(TechModel, on_delete=models.CASCADE, related_name="unlocked_by")
    die = models.ForeignKey(DieModel, on_delete=models.CASCADE)
    dots = models.IntegerField()

    def costText(self):
        resources = [f"{self.dots}x {self.die.label} kostka"]
        resources += [f"{r.amount}x {r.resource.label}" for r in self.resources.all()]
        return ", ".join(resources)

    def getInputs(self):
        return {item.resource: item.amount for item in self.resources.all()}

class TechEdgeInputModel(models.Model):
    parent = models.ForeignKey(TechEdgeModel, on_delete=models.CASCADE, related_name="resources")
    resource = models.ForeignKey(ResourceModel, on_delete=models.CASCADE)
    amount = models.IntegerField(validators=[MinValueValidator(0)])


