from django import forms

from game.forms.action import MoveForm
from game.models.actionMovesList import ActionMove
from game.models.actionBase import Action

from game.data.tech import TechModel



class SetBuildingDistanceForm(MoveForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        buildings = self.state.teamState(self.teamId).techs.getBuildings()
        choices = [(x.id, x.label) for x in buildings]
        self.fields["source"] = \
            forms.ChoiceField(choices=choices, label="První budova")
        self.fields["target"] = \
            forms.ChoiceField(choices=choices, label="Druhá budova")
        self.fields["distance"] = forms.IntegerField(min_value=0, label="Vzdálenost")

class SetBuildingDistanceMove(Action):
    class Meta:
        proxy = True
    class CiviMeta:
        move = ActionMove.setBuildingDistance
        form = SetBuildingDistanceForm
        allowed = ["super", "org"]

    @staticmethod
    def relevantEntities(state, team):
        return []

    def build(data):
        action = SetBuildingDistanceMove(
            team=data["team"],
            move=data["action"],
            arguments=Action.stripData(data))
        return action

    def initiate(self, state):
        return True, ""

    def commit(self, state):
        distLogger = state.teamState(self.team.id).distances
        source = TechModel.objects.get(id=self.arguments["source"])
        target = TechModel.objects.get(id=self.arguments["target"])
        distance = self.arguments["distance"]
        distLabel = f"{source.label}&harr;{target.label}"
        try:
            originalDistance = distLogger.getBuildingDistance(source, target)
            if originalDistance <= distance:
                message = f"""
                    Původní vzdálenost pro {distLabel} ({originalDistance}) je menší než nová ({distance}).<br>
                    Vzdálenost nelze aktualizovat.
                """
                return False, message
            distanceMessage = f"Původní vzdálenost {distLabel}: <b>{originalDistance}</b>"
        except RuntimeError:
            distanceMessage = f"Původní vzdálenost {distLabel}: <b>neznámá</b>"
        distLogger.setBuildingDistance(source, target, distance)
        message = f"""{distanceMessage}<br>
            Nová vzdálenost: <b>{distance}</b>"""
        return True, message