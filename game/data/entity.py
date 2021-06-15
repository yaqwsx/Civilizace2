from django.db import models
import django_enumfield
from game.utils import classproperty
from django_enumfield import enum
import copy
import types

class EntitiesVersionManager(models.Manager):
    def getNewest(self):
        return self.latest("pk")

class EntitiesVersion(models.Model):
    created = models.DateTimeField(auto_now_add=True)

    objects = EntitiesVersionManager()

class EntityManager(models.Manager):
    def fixVersionManger(self, version):
        """
        Return a new manager that returns entities on given version
        """
        s = super(EntityManager, self)
        def get_queryset(self):
            return s.get_queryset().filter(version=version.id)
        newManager = copy.copy(self)
        newManager.get_queryset = types.MethodType(get_queryset, newManager)
        return newManager

    def latest(self):
        return self.get_queryset().filter(version=EntitiesVersion.objects.getNewest())

class FakeEntityManager(models.Manager):
    """
    There are some models (e.g., tasks) that are useful to be treated like
    entities, but they are not versioned. Let's give them the same interface
    """
    def fixVersionManger(self, version):
        return self

    def latest(self):
        return self

class EntityModel(models.Model):
    syntheticId = models.AutoField(primary_key=True)
    id = models.CharField(max_length=20)
    label = models.CharField(max_length=50)
    version = models.ForeignKey(EntitiesVersion, on_delete=models.CASCADE)

    @classproperty
    def objects(self):
        raise NotImplementedError(
            "You tried to access entity manager without "
            "specifying entity version. Use action context!")

    manager = EntityManager()

    class Meta:
        # constraints = [
        #     models.UniqueConstraint(name="%(class)s_pk", fields=["id", "version"])
        # ]
        unique_together = (("id", "version"),)

    def __str__(self):
        return self.id

class DieModel(EntityModel):
    def color(self):
        """ Return color for the die in hex code string """
        colors = {
            "die-sila": "2884c9", # Blue
            "die-prir": "949494", # Gray
            "die-spol": "e3b510", # Orange
            "die-tech": "4e9c00", # Green
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

class Direction(enum.Enum):
    North = 0
    West = 1
    South = 2
    East = 3

    @property
    def opposite(self):
        return Direction((self.value + 2) % 4)

    @property
    def correspondingDie(self):
        return {
            Direction.North: "die-sila",
            Direction.West: "die-prir",
            Direction.South: "die-spol",
            Direction.East: "die-tech"
        }[self.value]

class IslandModel(EntityModel):
    direction = enum.EnumField(Direction)
    distance = models.IntegerField()
    root = models.ForeignKey("TechModel", on_delete=models.CASCADE, null=True)

    def isOnCoords(self, direction, distance):
        if self.distance > 24 or self.distance < 1:
            raise RuntimeError("Unsupported distance")
        onOriginal = self.direction == direction and self.distance == distance
        onAlternate = direction.opposite == self.direction and (24 - distance) == self.distance
        return onOriginal or onAlternate

