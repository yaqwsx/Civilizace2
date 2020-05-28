from django import forms
from .fields import EmptyEnumChoiceField, TeamChoiceField, captures
from game.models.actionMovesList import ActionMove
from game.models.actionMoves import *
from game.models.actionBase import Action
from game.models.keywords import KeywordType
from django.core.validators import MaxValueValidator, MinValueValidator
from game.models.users import Team

class DiceThrowForm(forms.Form):
    dice = forms.ChoiceField(label="Použitá kostka")
    throwCount = forms.IntegerField(label="Počet hodů kostkou", initial=0,
        validators=[MinValueValidator(0)])
    dotsCount = forms.IntegerField(label="Počet hozených puntíků:", initial=0,
        validators=[MinValueValidator(0)])

    def __init__(self, allowedDices, *args, **kwargs):
        super(DiceThrowForm, self).__init__(*args, **kwargs)
        self.fields["dice"].choices = [(x, x.label) for x in allowedDices]

class MoveInitialForm(forms.Form):
    team = captures(KeywordType.team,
        TeamChoiceField(label="Tým"))
    action = captures(KeywordType.move,
        EmptyEnumChoiceField(ActionMove, label="Akce"))
    entity = forms.ChoiceField(required=False, label="Entita")
    canceled = forms.BooleanField(widget=forms.HiddenInput(), required=False, initial=False)

    def __init__(self, data=None, state=None, **kwargs):
        if data:
            super().__init__(data)
        else:
            super().__init__(**kwargs)

        teams = Team.objects.all()
        self.allEntities = set()
        self.teamAllowedEntities = {team.id: set() for team in teams}
        self.actionEntities = {action.CiviMeta.move: set() for action in Action.__subclasses__()}
        self.actionForEntity = {}
        for action in Action.__subclasses__():
            for team in teams:
                entities = action.relevantEntities(state, team)
                self.teamAllowedEntities[team.id].update(entities)
                self.actionEntities[action.CiviMeta.move].update(entities)
                self.allEntities.update(entities)
                for entity in entities:
                    self.actionForEntity[entity] = action.CiviMeta.move
        self.fields["entity"].choices = [('', '-----------')] + [(entity.id, entity.label) for entity in self.allEntities]


# Base form for building actions - every other move building form has to inherit
# from this one
class MoveForm(MoveInitialForm):
    def __init__(self, team=None, action=None, entity=None, data=None, state=None):
        self.teamId = team
        self.state = state
        if data:
            super(MoveForm, self).__init__(data, state=state)
            self.entityId = data.get("entity")
        else:
            super(MoveForm, self).__init__(initial={
                    "action": action,
                    "team": team,
                    "entity": entity,
                }, state=state)
            self.entityId = entity
        for fieldName in ["action", "team", "entity"]:
            self.fields[fieldName].widget = forms.HiddenInput()


