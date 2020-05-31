import math
from django import forms
from django.core.validators import MaxValueValidator, MinValueValidator

from game.data.vyroba import VyrobaModel
from game.forms.action import MoveForm
from game.models.actionBase import Action
from game.models.actionMovesList import ActionMove
from game.models.state import ResourceStorage


class VyrobaForm(MoveForm):
    costLabel = forms.CharField(widget=forms.Textarea)
    volumeSelect = forms.IntegerField(label="Počet jednotek", validators=[MinValueValidator(1), MaxValueValidator(5)])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        vyroba = VyrobaModel.objects.get(id=self.entityId)
        self.fields["costLabel"].initial = str(list(vyroba.inputs.all()))

class VyrobaMove(Action):
    class Meta:
        proxy = True
    class CiviMeta:
        move = ActionMove.vyroba
        form = VyrobaForm

    @staticmethod
    def build(data):
        action = VyrobaMove(
            team=data["team"],
            move=data["action"],
            arguments={
                "entity": data["entity"],
                "volume": data["volumeSelect"]
        })
        return action

    @staticmethod
    def relevantEntities(state, team):
        techs = state.teamState(team.id).techs

        results = []
        results.extend(techs.getVyrobas())

        return results

    @property
    def volume(self):
        return self.arguments["volume"]

    vyroba = None
    def preprocess(self, state):
        self.teamState =  state.teamState(self.team.id)
        self.vyroba = VyrobaModel.objects.get(id=self.arguments["entity"])
        self.unitCost = list(self.vyroba.inputs.all())
        self.cost = {input.resource: input.amount*self.volume for input in self.unitCost}
        self.die = self.vyroba.die
        self.dots = math.ceil((self.vyroba.dots*self.volume+1)/2)

    def requiresDice(self, state):
        return True

    def dotsRequired(self, state):
        self.preprocess(state)
        return {self.die:self.dots}

    def initiate(self, state):
        self.preprocess(state)
        
        storage = self.teamState.resources
        
        materials = storage.payResources(self.cost)

        message = "Musíte zaplatit " + storage.asHtml(materials)
        print(message)
        return True, message


    def commit(self, state):
        self.preprocess(state)
        resources = {self.vyroba.output: self.vyroba.amount}
        materials = self.teamState.resources.receiveResources(resources)
        message = "Tým získal " + ResourceStorage.asHtml(resources) + "<br>" \
                  "<b>Vydej " + ResourceStorage.asHtml(materials) + "</b>"
        print("Vyroba commit message: " + message)
        return True, message

    def abandon(self, state):
        self.preprocess(state)

        productions = filter(
            lambda resource, amount:
                resource.id[:5] == "prod-"
                or resource.id == "res-obyvatel",
            self.cost.items()
        )

        message = self.abandonMessage()
        message += "<br>"
        message += "Tým nedostane zpátky žádné materiály"
        return True, self.abandonMessage()

    def cancel(self, state):
        self.preprocess(state)
        materials = self.teamState.resources.receiveResources(self.cost)

        message = self.cancelMessage()
        message += "<br>"
        message += "Vraťte týmu materiály: " + ResourceStorage.asHtml(materials)

        return True, message