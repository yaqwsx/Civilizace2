from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset

from django import forms

from game.forms.action import MoveForm
from game.models.actionBase import Action
from game.models.actionMovesList import ActionMove


class SandboxForm(MoveForm):
    jabkaSelect = forms.IntegerField(label="Počet jablek")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                'first arg is the legend of the fieldset',
                'like_website',
                'favorite_number',
                'favorite_color',
                'favorite_food',
                'notes'
            )
        )

class SandboxMove(Action):
    class Meta:
        proxy = True
    class CiviMeta:
        move = ActionMove.sandbox
        form = SandboxForm

    @staticmethod
    def build(data):
        action = SandboxMove(
            team=data["team"],
            move=data["action"],
            arguments={
        })
        return action

    @staticmethod
    def relevantEntities(state, team):
        return []
