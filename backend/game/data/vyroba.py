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

    def getInputs(self):
        results = {item.resource:item.amount for item in self.inputs.all()}
        return results

    def getOutput(self):
        return {self.output:self.amount}

class VyrobaInputModel(models.Model):
    parent = models.ForeignKey(VyrobaModel, on_delete=models.CASCADE, related_name="inputs")
    resource = models.ForeignKey(ResourceModel, on_delete=models.CASCADE, related_name="input_to_vyrobas")
    amount = models.IntegerField(validators=[MinValueValidator(0)])

    def __str__(self):
        return self.resource.id + ":" + str(self.amount)

class VyrobaEnhancedImage:
    def __init__(self, vyroba, enhancers):
        self.id = vyroba.id
        self.label = vyroba.label
        self.flavour = vyroba.flavour
        self.tech = vyroba.tech
        self.build = vyroba.build
        self.output = vyroba.output
        self.amount = vyroba.amount
        self.die = vyroba.die
        self.dots = vyroba.dots
        self.inputs = dict(vyroba.getInputs())
        self.output = vyroba.output

        self.vyroba = vyroba
        self.enhancers = enhancers

        for enhancer in enhancers:
            self.amount += enhancer.amount
            for resource, amount in enhancer.getUseInputs().items():
                amount += self.inputs.get(resource, 0)
                self.inputs[resource] = amount

    def getInputs(self):
        return self.inputs

    def getOutput(self):
        return {self.output:self.amount}