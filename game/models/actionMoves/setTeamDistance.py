from django import forms
from crispy_forms.layout import Layout, Fieldset, HTML
import json

from game.forms.action import MoveForm
from game.models.actionMovesList import ActionMove
from game.models.actionBase import Action, InvalidActionException
from game.models.users import Team

from game.data.tech import TechModel
from game.models.state import MissingDistanceError


class SetTeamDistanceForm(MoveForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        distanceLogger = self.state.teamState(self.teamId).distances
        for team in Team.objects.all():
            if team.id == self.teamId:
                continue
            try:
                distance = distanceLogger.getTeamDistance(team)
                self.fields[f'team{team.id}'] = forms.IntegerField(
                    label=team.name,
                    initial=distance,
                    max_value=distance,
                    min_value=0)
            except MissingDistanceError:
                self.fields[f'team{team.id}'] = forms.IntegerField(
                    label=team.name,
                    min_value=0,
                    required=False)
    def clean(self):
        c = super().clean()
        for team in Team.objects.all():
            if f'team{team.id}' in c:
                c[team.id] = c[f'team{team.id}']
                del c[f'team{team.id}']
        return c

class SetTeamDistanceMove(Action):
    class Meta:
        proxy = True
    class CiviMeta:
        move = ActionMove.setTeamDistance
        form = SetTeamDistanceForm
        allowed = ["super", "org"]

    @staticmethod
    def relevantEntities(state, team):
        return []

    def build(data):
        action = SetTeamDistanceMove(
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
        messages = []
        distances = {}
        for team in Team.objects.all():
            if team.id == self.team.id:
                continue
            if team.id not in self.arguments:
                return False, f"Chybí vzdálenostní informace pro tým {team.name}"
            distance = self.arguments[team.id]
            if not distance:
                continue
            try:
                originalDistance = distLogger.getTeamDistance(team)
                if originalDistance < distance:
                    messages.append(f"""
                        Původní vzdálenost pro {team.name} ({originalDistance}) je menší než nová ({distance}).<br>
                        Vzdálenost nelze aktualizovat.
                    """)
                else:
                    distLogger.setTeamDistance(team, distance)
                    if distance != originalDistance:
                        distances[team] = (originalDistance, distance)
            except MissingDistanceError:
                distLogger.setTeamDistance(team, distance)
                distances[team] = (None, distance)
        if messages:
            errors = "".join([f'<li>{x}</li>' for x in messages])
            return False, f'Nelze zaktualizovat vzdálenosti: <ul class="list-disc px-4">{errors}</ul>'
        msg = "".join([f'<li>{team.name}: {self.formatDistanceChange(change)}' for team, change in distances.items()])
        return True, f'Následující vzdálenosti budou aktualizovány:  <ul class="list-disc px-4">{msg}</ul>'