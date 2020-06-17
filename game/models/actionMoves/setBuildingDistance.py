from django import forms
from crispy_forms.layout import Layout, Fieldset, HTML
import json

from game.forms.action import MoveForm
from game.models.actionMovesList import ActionMove
from game.models.actionBase import Action
from game.models.state import MissingDistanceError

from game.data.tech import TechModel


class SetBuildingDistanceForm(MoveForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        distanceLogger = self.state.teamState(self.teamId).distances
        buildings = self.state.teamState(self.teamId).techs.getBuildings()
        sort(buildings, key=lambda x: x.label)
        sourceBuilding = TechModel.objects.get(id=self.entityId)
        for b in buildings:
            if b.id == self.entityId:
                continue
            try:
                distance = distanceLogger.getBuildingDistance(sourceBuilding, b)
                self.fields[b.id] = forms.IntegerField(
                    label=b.label,
                    initial=distance,
                    max_value=distance,
                    min_value=0)
            except MissingDistanceError:
                self.fields[b.id] = forms.IntegerField(
                    label=b.label,
                    min_value=0,
                    required=False)

class SetBuildingDistanceMove(Action):
    class Meta:
        proxy = True
    class CiviMeta:
        move = ActionMove.setBuildingDistance
        form = SetBuildingDistanceForm
        allowed = ["super", "org"]

    @staticmethod
    def relevantEntities(state, team):
        return sorted(state.teamState(team).techs.getBuildings(), key=lambda x: x.label)

    def build(data):
        action = SetBuildingDistanceMove(
            team=data["team"],
            move=data["action"],
            arguments=Action.stripData(data))
        return action

    def initiate(self, state):
        return True, ""

    def formatDistanceChange(self, change):
        if change[0]:
            return f'{change[0]} &rarr; {change[1]}'
        return f'Neznámá &rarr; {change[1]}'

    def commit(self, state):
        distLogger = state.teamState(self.team.id).distances
        source = TechModel.objects.get(id=self.arguments["entity"])
        buildings = state.teamState(self.team.id).techs.getBuildings()
        messages = []
        distances = {}
        for b in buildings:
            if b.id == source.id:
                continue
            if b.id not in self.arguments:
                return False, f"Chybí vzdálenostní informace pro budovu {b.label}"
            distance = self.arguments[b.id]
            if not distance:
                continue
            try:
                originalDistance = distLogger.getBuildingDistance(source, b)
                if originalDistance < distance:
                    messages.append(f"""
                        Původní vzdálenost pro {b.label} ({originalDistance}) je menší než nová ({distance}).<br>
                        Vzdálenost nelze aktualizovat.
                    """)
                else:
                    distLogger.setBuildingDistance(source, b, distance)
                    if distance != originalDistance:
                        distances[b] = (originalDistance, distance)
            except MissingDistanceError:
                distLogger.setBuildingDistance(source, b, distance)
                distances[b] = (None, distance)
        if messages:
            errors = "".join([f'<li>{x}</li>' for x in messages])
            return False, f'Nelze zaktualizovat vzdálenosti: <ul class="list-disc px-4">{errors}</ul>'
        msg = "".join([f'<li>{source.label}&harr;{b.label}: {self.formatDistanceChange(change)}' for b, change in distances.items()])
        return True, f'Následující vzdálenosti budou aktualizovány:  <ul class="list-disc px-4">{msg}</ul>'