from django import forms

from game.forms.action import MoveForm
from game.models.actionTypeList import ActionType
from game.models.actionBase import Action, InvalidActionException, ActionResult
from game.models.state import ResourceStorage


class MaaraForm(MoveForm):
    valueSelect = forms.IntegerField(label="Vyber cislo")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["valueSelect"].initial = 42

class MaaraMove(Action):
    class Meta:
        proxy = True
    class CiviMeta:
        move = ActionType.maaraCounter
        form = MaaraForm
        allowed = ["super", "org"]

    @staticmethod
    def build(data):
        action = MaaraMove(
            team=data["team"],
            move=data["action"],
            arguments=Action.stripData(data))
        return action

    @staticmethod
    def relevantEntities(state, team):
        return []

    def requiresDice(self, state):
        return False


    def initiate(self, state):
        result = ActionResult.makeSuccess("Success")
        return result

    def commit(self, state):
        return ActionResult.makeSuccess("Commit successfullllllll")

    def abandon(self, state):
        raise NotImplementedError()

    def cancel(self, state):
        raise NotImplementedError()
