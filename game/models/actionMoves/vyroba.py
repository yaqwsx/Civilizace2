import math
from django import forms
from django.core.validators import MaxValueValidator, MinValueValidator

from game.data.vyroba import VyrobaModel
from game.forms.action import MoveForm
from game.models.actionBase import Action
from game.models.actionMovesList import ActionMove


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
        self.dots = math.ceil((self.vyroba.dots+1)/2)

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

    def abandon(self, state):
        # TODO: Implement
        return True, self.abandonMessage()

    def cancel(self, state):
        # TODO: Implement
        return True, self.cancelMessage()