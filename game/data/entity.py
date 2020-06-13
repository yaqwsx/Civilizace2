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
    def color(self):
        """ Return color for the die in hex code string """
        colors = {
            "die-plane": "2884c9", # Blue
            "die-hory": "949494", # Gray
            "die-poust": "e3b510", # Orange
            "die-les": "4e9c00", # Green
            "die-any": "000000" # Black
        }
        colors.update({
            # "die-plane": "eeeeee", # Blue
            # "die-hory": "eeeeee", # Gray
            # "die-poust": "eeeeee", # Orange
            # "die-les": "eeeeee", # Green
            # "die-any": "eeeeee" # Black
        })
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