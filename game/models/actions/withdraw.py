from crispy_forms.layout import Layout, Fieldset, HTML

from django import forms
from django.core.validators import MinValueValidator, MaxValueValidator

from game.data import ResourceModel
from game.forms.action import MoveForm
from game.models.actionBase import Action, ActionResult
from game.models.actionTypeList import ActionType


class WithdrawForm(MoveForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        team = self.state.teamState(self.teamId)
        resources = team.materials

        fields = [f"Můžete vyzvednout až {team.resources.getWork()} jednotek materiálů"]

        for item in resources.asMap().items():
            resource = item[0]
            amount = item[1]
            if amount < 0:
                self.fields[resource.id] = forms.IntegerField(
                    label=f"{resource.htmlRepr()} (max. 0&times;)",
                    validators=[MinValueValidator(0), MaxValueValidator(0)],
                    initial=0)
            else:
                self.fields[resource.id] = forms.IntegerField(
                    label=f"{resource.htmlRepr()} (max. {amount}&times;)",
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
        move = ActionType.withdraw
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
        team = self.teamState(state)
        message = ["Vydat materiály:"]

        materials = {}
        spentWork = 0

        for key in filter(lambda x: x[:4] in  ["mat-"], self.arguments.keys()):
            if not self.arguments[key]:
                continue
            resource = self.context.resources.get(id=key)
            amount = self.arguments[key]
            materials[resource] = amount
            spentWork += amount
            message.append(f"  {amount}x {resource.htmlRepr()}")

        team.materials.payResources(materials)
        team.resources.spendWork(spentWork)
        message.append(f"Výběr materiálu stojí <b>{spentWork}&times; Práce</b>")

        self.arguments["team"] = None
        return ActionResult.makeSuccess( "<br>".join(message))

    def commit(self, state):
        return ActionResult.makeSuccess("")
