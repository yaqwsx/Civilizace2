from crispy_forms.layout import Layout, Fieldset, HTML

from django import forms

from game.forms.action import MoveForm
from game.models.actionBase import Action
from game.models.actionMovesList import ActionMove


class SandboxForm(MoveForm):
    jabkaSelect = forms.IntegerField(label="Počet jablek")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # self.fields['extra_field_count'].initial = 1

        # self.fields['extra_field_hrusky'] = forms.CharField()
        self.fields["hruskySelect"] = forms.IntegerField(label="Počet hrusek")
        print("Added hrusky")

        self.helper.layout = Layout(
            self.commonLayout, # Don't forget to add fields of the base form
            Fieldset(
                'Toto je popisek skupiny',
                'jabkaSelect',
                'hruskySelect'
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
        print("Sandbox build arguments: " + str(data))
        action = SandboxMove(
            team=data["team"],
            move=data["action"],
            arguments=dict(data)
        )
        return action

    @staticmethod
    def relevantEntities(state, team):
        return []

    def initiate(self, state):
        print("initiate.arguments: " + str(self.arguments))

