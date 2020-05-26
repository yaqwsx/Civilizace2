from django import forms
from .fields import EmptyEnumChoiceField, TeamChoiceField, captures
from game.models.actionMovesList import ActionMove
from game.models.keywords import KeywordType
from django.core.validators import MaxValueValidator, MinValueValidator

class DiceThrowForm(forms.Form):
    dice = forms.ChoiceField(label="Použitá kostka")
    throwCount = forms.IntegerField(label="Počet hodů kostkou", initial=0,
        validators=[MinValueValidator(0)])
    dotsCount = forms.IntegerField(label="Počet hozených puntíků:", initial=0,
        validators=[MinValueValidator(0)])

    def __init__(self, allowedDices, *args, **kwargs):
        super(DiceThrowForm, self).__init__(*args, **kwargs)
        self.fields["dice"].choices = [(x.id, x.label) for x in allowedDices]

class MoveInitialForm(forms.Form):
    action = captures(KeywordType.move,
        EmptyEnumChoiceField(ActionMove, label="Akce"))
    team = captures(KeywordType.team,
        TeamChoiceField(label="Tým"))
    canceled = forms.BooleanField(widget=forms.HiddenInput(), required=False, initial=False)

# Base form for building actions - every other move building form has to inherit
# from this one
class MoveForm(MoveInitialForm):
    def __init__(self, team=None, action=None, data=None, state=None, *args, **kwargs):
        if data:
            super(MoveForm, self).__init__(data)
        else:
            super(MoveForm, self).__init__(initial={
                    "action": action,
                    "team": team
                }, *args, **kwargs)
        for fieldName in ["action", "team"]:
            self.fields[fieldName].widget = forms.HiddenInput()
