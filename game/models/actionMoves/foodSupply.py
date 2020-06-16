from crispy_forms.layout import Layout, Fieldset, HTML
from django import forms
from django.core.validators import MinValueValidator, MaxValueValidator

from game.data import ResourceModel
from game.forms.action import MoveForm
from game.models.actionBase import Action
from game.models.actionMovesList import ActionMove


class FoodSupplyForm(MoveForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        fields = ['Vyberte produkce, které přesměrovat na tržiště']
        layoutData = [self.commonLayout]

        resources = self.state.teamState(self.teamId).resources

        for resource, amount in resources.getResourcesByType(ResourceModel.objects.get(id="prod-jidlo-2")).items():
            self.fields[resource.id] = forms.IntegerField(
                label=f"{resource.htmlRepr()} (max. {amount}x)",
                validators=[MinValueValidator(0), MaxValueValidator(amount)],
                initial=0)
            fields.append(resource.id)

        layoutData.append(Fieldset(*fields))
        self.helper.layout = Layout(*layoutData)

class FoodSupplyMove(Action):
    class Meta:
        proxy = True
    class CiviMeta:
        move = ActionMove.foodSupply
        form = FoodSupplyForm
        allowed = ["super", "org"]

    @staticmethod
    def relevantEntities(state, team):
        return []

    def build(data):
        action = FoodSupplyMove(team=data["team"], move=data["action"], arguments={**data})
        return action

    def initiate(self, state):

        team = self.teamState(state)
        message = ["Přesměrování produkcí do centra:"]

        transfer = {}

        for key in filter(lambda x: x[:5] ==  "prod-", self.arguments.keys()):
            if not self.arguments[key]:
                continue
            resource = ResourceModel.objects.get(id=key)
            transfer[resource] = self.arguments[key]
            message.append(f"  {self.arguments[key]}x {resource.htmlRepr()}")

        team.resources.payResources(transfer)

        team.foodSupply.addSupply(transfer)

        self.arguments["team"] = None
        return True, "<br>".join(message)

    def commit(self, state):
        return True, ""

