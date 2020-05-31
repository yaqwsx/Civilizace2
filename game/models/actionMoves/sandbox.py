from crispy_forms.layout import Layout, Fieldset, HTML

from django import forms

from game.forms.action import MoveForm
from game.models.actionBase import Action
from game.models.actionMovesList import ActionMove


class SandboxForm(MoveForm):
    jabkaSelect = forms.IntegerField(label="Počet jablek")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper.layout = Layout(
            self.commonLayout, # Don't forget to add fields of the base form
            Fieldset(
                'Toto je popisek skupiny',
                'jabkaSelect',
            ),
            HTML("""A tady je prostě libovolné HTML, např. čára: <hr class="border-2 border-black my-2">""")
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
