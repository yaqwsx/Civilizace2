from django.db import models

class GameDataModel(models.Model):
    pass


class EntityModel(models.Model):
    id = models.CharField(max_length=20, primary_key=True)
    label = models.CharField(max_length=50)
    data = models.ForeignKey(GameDataModel, on_delete=models.CASCADE)
    class Meta:
        abstract = True

    def __str__(self):
        return self.id

class DieModel(EntityModel):
    pass