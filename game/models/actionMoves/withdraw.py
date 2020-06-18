from crispy_forms.layout import Layout, Fieldset, HTML

from django import forms
from django.core.validators import MinValueValidator, MaxValueValidator

from game.data import ResourceModel
from game.forms.action import MoveForm
from game.models.actionBase import Action
from game.models.actionMovesList import ActionMove


class WithdrawForm(MoveForm):
    jabkaSelect = forms.IntegerField(label="Počet jablek")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        team = self.state.teamState(self.teamId)
        resources = team.materials

        fields = [f"Můžete vyzvednout {team.resources.getWork()} jednotek materiálů"]

        for item in resources.items:
            resource = item.resource
            amount = item.amount
            self.fields[resource.id] = forms.IntegerField(
                label=f"{resource.htmlRepr()} (max. {amount}x)",
                validators=[MinValueValidator(0), MaxValueValidator(amount)],
                initial=0)
            fields.append(resource.id)

        layoutData = [self.commonLayout]
        layoutData.append(Fieldset(*fields))
        self.helper.layout = Layout(*layoutData)

class WithdrawMove(Action):
    class Meta:
        proxy = True
    class CiviMeta:
        move = ActionMove.withdraw
        form = WithdrawForm
        allowed = ["super", "org"]

    @staticmethod
    def build(data):
        action = WithdrawMove(
            team=data["team"],
            move=data["action"],
            arguments={**data})
        return action

    @staticmethod
    def relevantEntities(state, team):
        return []

    def initiate(self, state):
        print("Initiate")
        team = self.teamState(state)
        message = ["Vyzvednuté materiály:"]

        materials = {}

        for key in filter(lambda x: x[:5] ==  "prod-", self.arguments.keys()):
            if not self.arguments[key]:
                continue
            resource = ResourceModel.objects.get(id=key)
            materials[resource] = self.arguments[key]
            message.append(f"  {self.arguments[key]}x {resource.htmlRepr()}")

        team.materials.payResources(materials)

        self.arguments["team"] = None
        return True, "<br>".join(message)

    def commit(self, state):
        print("Commit")
        return True, ""
