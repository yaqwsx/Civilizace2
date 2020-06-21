import math
from crispy_forms.layout import Layout, Fieldset, HTML

from django import forms
from django.core.validators import MinValueValidator, MaxValueValidator

from game.data import ResourceModel
from game.forms.action import MoveForm
from game.models.actionBase import Action
from game.models.actionMovesList import ActionMove
from game.models.state import MissingDistanceError, InvalidActionException
from game.models.users import Team

from game.forms.fields import TeamChoiceField


class AttackForm(MoveForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        otherTeam = self.getEntity(Team)
        if otherTeam.id == self.teamId:
            raise InvalidActionException("Nemůžete účotičt sami na sebe")

        productions = self.state.teamState(otherTeam).resources
        materials = self.state.teamState(otherTeam).materials

        storageItems = [ f'{res.htmlRepr()}: Produkuje {amount}&times;, je možné ukrást {materials.getAmount(res.getMaterial()) + amount}' for res, amount in productions.getAll().items() if res.isProduction ]
        storageMsg = '<ul class="list-disc px-5">' + "".join([f'<li>{x}</li>' for x in storageItems]) + '</ul>'

        self.fields["production"] = forms.ChoiceField(label="Vyberte produkci",
            choices=[(res.id, res.label) for  res in productions.getAll() if res.isProduction])
        self.fields["amount"] = forms.IntegerField(label="Množství", min_value=1, initial=1)

        self.helper.layout = Layout(
            self.commonLayout,
            HTML(storageMsg),
            "production",
            "amount"
        )

class AttackMove(Action):
    class Meta:
        proxy = True
    class CiviMeta:
        move = ActionMove.attack
        form = AttackForm
        allowed = ["super", "org"]

    @staticmethod
    def build(data):
        action = AttackMove(
            team=data["team"],
            move=data["action"],
            arguments=Action.stripData(data))
        return action

    @staticmethod
    def relevantEntities(state, team):
        return Team.objects.all()

    def initiate(self, state):
        oTeam = Team.objects.get(id=self.arguments["entity"])
        oTeamState = state.teamState(oTeam)
        production = ResourceModel.objects.get(id=self.arguments["production"])
        prodAmount = oTeamState.resources.getAmount(production)
        currentAmount = oTeamState.materials.getAmount(production.getMaterial())
        print(f"Current amount {currentAmount}")
        if currentAmount - self.arguments["amount"] < -prodAmount:
            return False, f'Nemůžu plenit {self.arguments["amount"]}, jelikož by to bylo moc'
        oTeamState.materials.setAmount(production.getMaterial(), currentAmount - self.arguments["amount"])
        return True, f'Bude vyplněneno, vydej {self.arguments["amount"]}&times; {production.getMaterial().htmlRepr()}'

    def commit(self, state):
        return True, ""
