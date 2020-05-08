from django.db import models

class DieModel(models.Model):
    label = models.CharField(max_length=100)
    tag = models.CharField(max_length=20)

    def __init__(self, *args, **kwargs ):
        super(DieModel, self).__init__(*args, **kwargs)
        self.tag = kwargs["tag"]
        self.label = kwargs["label"]

class EntitiesModel(models.Model):
    class Manager(models.Manager):
        def create(self):
            dieLes = DieModel(tag="die-les", label="Lesní")
            dieLes.save()
            parent = super(EntitiesModel.Manager, self)

            # diePoust = DieModel(tag="die-poust", label="Pouštní")
            # diePlan = DieModel(tag="die-plane", label="Planinná")
            # dieHory = DieModel(tag="die-hory", label="Horská")
            # return parent.create(dieLes=dieLes, diePoust=diePoust, diePlan=diePlan, dieHory=dieHory)

            return parent.create(dieLes=dieLes)

    objects = Manager()
    dieLes = models.ForeignKey(DieModel, on_delete=models.CASCADE, related_name="les")

    # diePoust = models.ForeignKey(DieModel, on_delete=models.CASCADE, related_name="poust")
    # diePlan = models.ForeignKey(DieModel, on_delete=models.CASCADE, related_name="plan")
    # dieHory = models.ForeignKey(DieModel, on_delete=models.CASCADE, related_name="hory")
