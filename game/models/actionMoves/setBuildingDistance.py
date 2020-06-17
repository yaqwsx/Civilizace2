from django import forms
from crispy_forms.layout import Layout, Fieldset, HTML
import json

from game.forms.action import MoveForm
from game.models.actionMovesList import ActionMove
from game.models.actionBase import Action
from game.models.state import MissingDistanceError

from game.data.tech import TechModel


def preFillDistances(source, target, distance, distances):
    fmtDist = []
    for b, dist in distances.items():
        fmtDist.append([b[0].id, b[1].id, dist])

    return r'''
    <script>
        var source = document.getElementById("''' + source.id_for_label + r'''");
        var target = document.getElementById("''' + target.id_for_label + r'''");
        var distance = document.getElementById("''' + distance.id_for_label + r'''")

        var distances = ''' + json.dumps(fmtDist) + r''';
        function update() {
            var src = source.value;
            var tgt = target.value;
            if (src == tgt) {
                distance.value = 0;
                return;
            }
            for (var i = 0; i != distances.length; i++ ) {
                var item = distances[i];
                if ( (item[0] == src && item[1] == tgt) || (item[1] == src && item[0] == tgt)) {
                    distance.value = item[2];
                    return;
                }
                distance.value = "";
            }
        }

        source.addEventListener("change", update);
        target.addEventListener("change", update);
        update();
    </script>
    '''

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

        distances = self.state.teamState(self.teamId).distances.allBuildingDistances()

        self.helper.layout = Layout(
            self.commonLayout,
            "source",
            "target",
            "distance",
            HTML(preFillDistances(self["source"], self["target"],
                self["distance"], distances))
        )

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
        except MissingDistanceError:
            distanceMessage = f"Původní vzdálenost {distLabel}: <b>neznámá</b>"
        distLogger.setBuildingDistance(source, target, distance)
        message = f"""{distanceMessage}<br>
            Nová vzdálenost: <b>{distance}</b>"""
        return True, message