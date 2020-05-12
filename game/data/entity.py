from django.db import models

class GameDataModel(models.Model):
    class Manager(models.Manager):
        def create(self):
            # dieLes = DieModel(id="die-les", label="Lesní")
            # dieLes.save()
            # diePoust = DieModel(id="die-poust", label="Pouštní")
            # diePoust.save()
            # diePlan = DieModel(id="die-plane", label="Planinná")
            # diePlan.save()
            # dieHory = DieModel(id="die-hory", label="Horská")
            # dieHory.save()
            return super(GameDataModel.Manager, self).create()
                # dieLes=dieLes, diePoust=diePoust, diePlan=diePlan, dieHory=dieHory)

    objects = Manager()

    # dieLes = models.ForeignKey(DieModel, on_delete=models.CASCADE, related_name="les")
    # diePoust = models.ForeignKey(DieModel, on_delete=models.CASCADE, related_name="poust")
    # diePlan = models.ForeignKey(DieModel, on_delete=models.CASCADE, related_name="plan")
    # dieHory = models.ForeignKey(DieModel, on_delete=models.CASCADE, related_name="hory")

class EntityModel(models.Model):
    id = models.CharField(max_length=20, primary_key=True)
    label = models.CharField(max_length=50)
    data = models.ForeignKey(GameDataModel, on_delete=models.CASCADE)
    class Meta:
        abstract = True

class DieModel(EntityModel):
    pass