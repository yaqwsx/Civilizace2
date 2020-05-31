from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator

from .resource import ResourceModel
from .tech import TechModel
from .entity import EntityModel, DieModel

class VyrobaModel(EntityModel):
    flavour = models.TextField()
    tech = models.ForeignKey(TechModel, on_delete=models.CASCADE, related_name="unlock_vyrobas")
    build = models.ForeignKey(TechModel, on_delete=models.CASCADE, related_name="building_vyrobas", null=True)
    output = models.ForeignKey(ResourceModel, on_delete=models.CASCADE, related_name="output_of_vyroba")
    amount = models.IntegerField(validators=[MinValueValidator(0)])
    die = models.ForeignKey(DieModel, on_delete=models.CASCADE)
    dots = models.IntegerField()


class VyrobaInputModel(models.Model):
    parent = models.ForeignKey(VyrobaModel, on_delete=models.CASCADE, related_name="inputs")
    resource = models.ForeignKey(ResourceModel, on_delete=models.CASCADE, related_name="input_to_vyrobas")
    amount = models.IntegerField(validators=[MinValueValidator(0)])

    def __str__(self):
        return self.resource.id + ":" + str(self.amount)
