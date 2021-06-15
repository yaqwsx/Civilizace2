from game.data.tech import TechModel
from game.data.entity import FakeEntityManager
from django.db import models


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
    techId = models.CharField(max_length=32)
    active = models.BooleanField(default=True)

    @property
    def tech(self):
        return TechModel.manager.latest().get(id=self.techId)

    class Meta:
        constraints = [
            models.UniqueConstraint(name="%(class)s_pk", fields=["task", "techId"])
        ]

class AssignedTask(models.Model):
    """
    Assigns task to a team for given tech. Once the model is created, it should
    not be deleted.
    """
    techId = models.CharField(max_length=32)
    team = models.ForeignKey("Team", on_delete=models.PROTECT)
    task = models.ForeignKey("TaskModel", on_delete=models.PROTECT, null=True)
    assignedAt = models.DateTimeField(auto_now=False)
    completedAt = models.DateTimeField(auto_now=False, default=None, null=True)

    @property
    def tech(self):
        return TechModel.manager.latest().get(id=self.techId)

    class Meta:
        constraints = [
            models.UniqueConstraint(name="%(class)s_team-task", fields=["task", "team"]),
            models.UniqueConstraint(name="%(class)s_team-tech", fields=["techId", "team"])
        ]