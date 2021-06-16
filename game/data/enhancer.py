from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator

from .resource import ResourceModel
from .tech import TechModel
from .vyroba import VyrobaModel
from .entity import EntityModel, DieModel

class EnhancerModel(EntityModel):
    flavour = models.TextField()
    detail = models.TextField()
    tech = models.ForeignKey(TechModel, on_delete=models.CASCADE, related_name="unlock_enhancers")
    vyroba = models.ForeignKey(VyrobaModel, on_delete=models.CASCADE, related_name="vyroba_enhancer", null=True)
    amount = models.IntegerField(validators=[MinValueValidator(0)])
    die = models.ForeignKey(DieModel, on_delete=models.CASCADE)
    dots = models.IntegerField()

    def getDeployInputs(self):
        results = {item.resource:item.amount for item in self.deploy_inputs.all()}
        return results

    def getUseInputs(self):
        results = {item.resource:item.amount for item in self.use_inputs.all()}
        return results

    def getOutput(self):
        return {self.vyroba.output: self.amount}


class EnhancerDeployInputModel(models.Model):
    parent = models.ForeignKey(EnhancerModel, on_delete=models.CASCADE, related_name="deploy_inputs")
    resource = models.ForeignKey(ResourceModel, on_delete=models.CASCADE, related_name="deploy_input_to_enhancements")
    amount = models.IntegerField(validators=[MinValueValidator(0)])

    def __str__(self):
        return self.resource.id + ":" + str(self.amount)

class EnhancerUseInputModel(models.Model):
    parent = models.ForeignKey(EnhancerModel, on_delete=models.CASCADE, related_name="use_inputs")
    resource = models.ForeignKey(ResourceModel, on_delete=models.CASCADE, related_name="use_input_to_enhancements")
    amount = models.IntegerField(validators=[MinValueValidator(0)])

    def __str__(self):
        return self.resource.id + ":" + str(self.amount)