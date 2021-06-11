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

class TaskModel(models.Model):
    name = models.TextField()
    teamDescription = models.TextField()
    orgDescription = models.TextField()
    capacity = models.IntegerField()

    # Let's pretend we are a versioned entity...
    objects = FakeEntityManager()
    manager = FakeEntityManager()

    @property
    def label(self):
        """
        Make it compliant with EntityModel
        """
        return self.name

    def htmlRepr(self):
        return f"Úkol: <b>{self.label}</b><br><i>{self.text}</i>"

    def getAvailableTasks(self, team):
        """
        Given a team, return a list of available tasks they can complete.
        """
        raise NotImplementedError("This has to be implemented!")

class TaskMapping(models.Model):
    """
    Assigns tasks to techs. The model should not be ever deleted, it can be only
    disabled by setting active to False.
    """
    task = models.ForeignKey("TaskModel", on_delete=models.PROTECT)
    tech = models.ForeignKey("TechModel", on_delete=models.PROTECT)
    active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(name="%(class)s_pk", fields=["task", "tech"])
        ]

class AssignedTask(models.Model):
    """
    Assigns task to a team for given tech. Once the model is created, it should
    not be deleted.
    """
    task = models.ForeignKey("TaskModel", on_delete=models.PROTECT)
    team = models.ForeignKey("Team", on_delete=models.PROTECT)
    tech = models.ForeignKey("TechModel", on_delete=models.PROTECT, null=True)
    assignedAt = models.DateTimeField(auto_now=False)
    completedAt = models.DateTimeField(auto_now=False, default=None, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(name="%(class)s_team-task", fields=["task", "team"]),
            models.UniqueConstraint(name="%(class)s_team-tech", fields=["tech", "team"])
        ]


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
            Direction.North: "die-plane",
            Direction.West: "die-hory",
            Direction.South: "die-poust",
            Direction.East: "die-les"
        }[self.value]

class IslandModel(EntityModel):
    direction = enum.EnumField(Direction)
    distance = models.IntegerField()
    root = models.ForeignKey("TechModel", on_delete=models.CASCADE)

    def isOnCoords(self, direction, distance):
        if self.distance > 24 or self.distance < 1:
            raise RuntimeError("Unsupported distance")
        onOriginal = self.direction == direction and self.distance == distance
        onAlternate = direction.opposite == self.direction and (24 - distance) == self.distance
        return onOriginal or onAlternate

