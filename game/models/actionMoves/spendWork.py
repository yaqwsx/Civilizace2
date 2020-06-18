from crispy_forms.layout import Layout, Fieldset, HTML

from django import forms

from game.forms.action import MoveForm
from game.models.actionBase import Action
from game.models.actionMovesList import ActionMove
from game.models.state import ResourceStorage


class SpendWorkForm(MoveForm):
    spendWork = forms.IntegerField(label="Utratit práci", initial=5)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class SpendWorkMove(Action):
    class Meta:
        proxy = True
    class CiviMeta:
        move = ActionMove.spendWork
        form = SpendWorkForm
        allowed = ["super", "org"]

    @staticmethod
    def build(data):
        action = SpendWorkMove(
            team=data["team"],
            move=data["action"],
            arguments={"spendWork": data["spendWork"]}
        )
        return action

    @staticmethod
    def relevantEntities(state, team):
        return []

    def initiate(self, state):
        work = self.arguments['spendWork']
        team = self.teamState(state)

        try:
            team.resources.spendWork(work)
            return True, "Zaplatí se " + str(self.arguments['spendWork']) + " Práce"
        except ResourceStorage.NotEnoughResourcesException:
            return False, "Nemáte dostatek práce"

    def commit(self, state):
        return True, ""