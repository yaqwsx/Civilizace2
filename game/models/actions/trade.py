from django.forms.fields import ChoiceField, IntegerField
from game.forms.fields import TeamChoiceField
import math
from crispy_forms.layout import Layout, Fieldset, HTML

from django import forms
from django.core.validators import MinValueValidator, MaxValueValidator

from game.data import ResourceModel
from game.forms.action import MoveForm
from game.models.actionBase import Action, ActionResult
from game.models.actionTypeList import ActionType
from game.models.state import MissingDistanceError, TeamState
from game.models.users import Team


class TradeForm(MoveForm):
    recipient = TeamChoiceField(label="Přijemce")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        team = self.state.teamState(self.teamId)
        resources = team.resources.getResourcesByType()

        layoutData = [self.commonLayout]
        layoutData.append("recipient")

        for resource, amount in resources.items():
            self.fields[resource.id] = forms.IntegerField(
                label=f"{resource.htmlRepr()} (max. {amount}x)",
                validators=[MinValueValidator(0), MaxValueValidator(amount)],
                initial=0)
            layoutData.append(resource.id)
        layoutData.append(HTML(
            """
            Zkontoluj:
            <ul>
                <li>Pokud tým obchoduje III, vzdálenost musí být menší než 100</li>
                <li>Pokud tým obchoduje IV, vzdálenost musí být menší než 60</li>
                <li>Pokud tým obchoduje V, vzdálenost musí být menší než 20</li>
                <li>Pokud tým obchoduje VI, vzdálenost musí být 0</li>
            </ul>
            """
        ))
        self.helper.layout = Layout(*layoutData)

class TradeMove(Action):
    class Meta:
        proxy = True
    class CiviMeta:
        move = ActionType.trade
        form = TradeForm
        allowed = ["super", "org"]

    @staticmethod
    def build(data):
        data["recipient"] = data["recipient"].pk
        action = TradeMove(
            team=data["team"],
            move=data["action"],
            arguments=Action.stripData(data))
        return action

    @staticmethod
    def relevantEntities(state, team):
        return []

    @property
    def recipient(self):
        return Team.objects.get(id=self.arguments["recipient"])

    def initiate(self, state):
        teamState = self.teamState(state)
        recipient = self.recipient
        if recipient == self.team:
            return ActionResult.makeFail("Nemůžu obchodovat sám se sebou")
        recipientState = state.teamState(recipient)

        message = []
        for key in filter(lambda x: x[:5] == "prod-", self.arguments.keys()):
            if not self.arguments[key]:
                continue
            resource = self.context.resources.get(id=key)
            amount = self.arguments[key]
            package = {resource: amount}
            teamState.resources.payResources(package)
            recipientState.resources.receiveResources(package)
            message.append(f"  {amount}x {resource.htmlRepr()}")

        mbeg = f"Tým {recipient.name} dostane:<br>"
        return ActionResult.makeSuccess(mbeg + "<br>".join(message))

    def commit(self, state):
        return ActionResult.makeSuccess("")

