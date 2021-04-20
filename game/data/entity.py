from django.db import models

class EntitiesVersion(models.Model):
    created = models.DateTimeField(auto_now_add=True)

class EntityModel(models.Model):
    id = models.CharField(max_length=20, primary_key=True)
    label = models.CharField(max_length=50)
    version = models.ForeignKey(EntitiesVersion, on_delete=models.CASCADE)

    class Meta:
        abstract = True
        constraints = [
            models.UniqueConstraint(name="%(class)s_pk", fields=["id", "version"])
        ]

    def __str__(self):
        return self.id

class DieModel(EntityModel):
    def color(self):
        """ Return color for the die in hex code string """
        colors = {
            "die-plane": "2884c9", # Blue
            "die-hory": "949494", # Gray
            "die-poust": "e3b510", # Orange
            "die-les": "4e9c00", # Green
            "die-any": "000000" # Black
        }
        return colors[self.id]

class AchievementModel(EntityModel):
    implementation = models.CharField(max_length=50)
    icon = models.CharField(max_length=50)
    orgMessage = models.CharField(max_length=2028)

    def achieved(self, state, team):
        from game import achievements
        if self.implementation == "":
            return False
        return getattr(achievements, self.implementation)(state, team)

class TaskModel(EntityModel):
    popis = models.CharField(max_length=100)
    text = models.TextField()

    def htmlRepr(self):
        return f"Úkol: <b>{self.label}</b><br><i>{self.text}</i>"

class IslandModel(EntityModel):
    pass
    # Maara: You should put anything specific to the island entity here