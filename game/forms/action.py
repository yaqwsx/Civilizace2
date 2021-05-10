from django import forms
from .fields import EmptyEnumChoiceField, TeamChoiceField, captures
from game.models.actionTypeList import ActionType
from game.models.actions import *
from game.models.actionBase import Action, InvalidActionException
from django.core.validators import MaxValueValidator, MinValueValidator
from django_enumfield.forms.fields import EnumChoiceField
from game.models.users import Team

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field

class DiceThrowForm(forms.Form):
    dice = forms.ChoiceField(label="Použitá kostka")
    throwCount = forms.IntegerField(label="Počet hodů kostkou", initial=0,
        validators=[MinValueValidator(0)])
    dotsCount = forms.IntegerField(label="Počet hozených bodů:", initial=0,
        validators=[MinValueValidator(0)])

    def __init__(self, allowedDices, *args, **kwargs):
        super(DiceThrowForm, self).__init__(*args, **kwargs)
        self.fields["dice"].choices = [(x, x.label) for x in allowedDices]
        if len(allowedDices) == 1:
            self.fields["dice"].widget = forms.HiddenInput()
            self.fields["dice"].initial = self.fields["dice"].choices[0][0]

class MoveInitialForm(forms.Form):
    team = captures("",
        TeamChoiceField(label="Tým"))
    action = captures("",
        EnumChoiceField(ActionType, label="Akce"))
    entity = forms.ChoiceField(required=False, label="Entita")
    canceled = forms.BooleanField(widget=forms.HiddenInput(), required=False, initial=False)

    def __init__(self, user, data=None, state=None, **kwargs):
        from game.models.actions import allowedActionTypes
        if data:
            super().__init__(data)
        else:
            super().__init__(**kwargs)

        self.helper = FormHelper()
        self.helper.form_tag = False

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
        self.fields["action"].choices = [('', '-----------')] + [(move.value, move.label) for move in allowedActionTypes(user)]
        self.commonLayout = Layout(
            Field('team'),
            Field('action'),
            Field('entity'),
            Field('canceled')
        )


# Base form for building actions - every other move building form has to inherit
# from this one
class MoveForm(MoveInitialForm):
    def __init__(self, user, team=None, action=None, entity=None, data=None, state=None):
        self.teamId = team
        self.state = state
        if data:
            super(MoveForm, self).__init__(data=data, user=user, state=state)
            self.entityId = data.get("entity")
        else:
            super(MoveForm, self).__init__(initial={
                    "action": action,
                    "team": team,
                    "entity": entity,
                }, state=state, user=user)
            self.entityId = entity
        for fieldName in ["action", "team", "entity"]:
            self.fields[fieldName].widget = forms.HiddenInput()

    def getEntity(self, entityType):
        if not self.entityId:
            raise InvalidActionException("Nezadali jste entitu.")
        try:
            return entityType.objects.get(id=self.entityId)
        except entityType.DoesNotExist:
            raise InvalidActionException(f"Vámi zadaná entita s ID <i>{self.entityId}</i> neexistuje")


