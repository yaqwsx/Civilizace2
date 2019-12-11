from django.db import models
from .fields import JSONField
from .immutable import ImmutableModel
from .managers import DefaultSelectOrPrefetchManager
import json

class Action(ImmutableModel):
    created = models.DateTimeField("Time of creating the action", auto_now=True)
    name = models.CharField("Name", max_length=100, null=True)

    def __str__(self):
        return json.dumps(self._dict)

class State(ImmutableModel):
    action = models.ForeignKey("Action", on_delete=models.PROTECT)
    worldState = models.ForeignKey("WorldState", on_delete=models.PROTECT)
    teamStates = models.ManyToManyField("TeamState")

    def __str__(self):
        return json.dumps(self._dict)

    # ManyToMany Field needs to prefetched in order to make immutable models to
    # work intuitively (otherwise the recursive saving does not work as you can
    # get different handles to models)
    objects = DefaultSelectOrPrefetchManager(prefetch_related=('teamStates',))

class WorldState(ImmutableModel):
    data = JSONField()

    def __str__(self):
        return json.dumps(self._dict)

class TeamState(ImmutableModel):
    team = models.ForeignKey("Team", on_delete=models.PROTECT)
    wealth = models.ForeignKey("WealthTeamState", on_delete=models.PROTECT)
    population = models.ForeignKey("PopulationTeamState", on_delete=models.PROTECT)

    def __str__(self):
        return json.dumps(self._dict)

class WealthTeamState(ImmutableModel):
    data = JSONField()

    def __str__(self):
        return json.dumps(self._dict)

class PopulationTeamState(ImmutableModel):
    data = JSONField()

    def __str__(self):
        return json.dumps(self._dict)
