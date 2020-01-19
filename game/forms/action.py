from django import forms
from .fields import EmptyEnumChoiceField, TeamChoiceField
from game.models import ActionMove

class MoveInitialForm(forms.Form):
    action = EmptyEnumChoiceField(ActionMove, label="Akce")
    team = TeamChoiceField(label="Tým")
    canceled = forms.BooleanField(widget=forms.HiddenInput(), required=False, initial=False)

# Base form for building actions - every other move building form has to inherit
# from this one
class MoveForm(MoveInitialForm):
    def __init__(self, team=None, action=None, data=None, *args, **kwargs):
        if data:
            super(MoveForm, self).__init__(data)
        else:
            super(MoveForm, self).__init__(initial={
                    "action": action,
                    "team": team
                }, *args, **kwargs)
        for fieldName in ["action", "team"]:
            self.fields[fieldName].widget = forms.HiddenInput()

class CreateInitialForm(MoveForm):
    pass

class SanboxIncreaseCounterForm(MoveForm):
    amount = forms.IntegerField(label="Změna počítadla o:")