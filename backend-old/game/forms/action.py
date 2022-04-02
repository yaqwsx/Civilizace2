from django import forms
from .fields import EmptyEnumChoiceField, TeamChoiceField, captures
from game.models.actionTypeList import ActionType
from game.models.actions import *
from game.models.actionBase import Action, InvalidActionException
from django.core.validators import MaxValueValidator, MinValueValidator
from django_enumfield.forms.fields import EnumChoiceField
from game.models.users import Team

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, HTML

from timeit import default_timer as timer


class DiceThrowForm(forms.Form):
    dice = forms.ChoiceField(label="Použitá kostka")
    throwCount = forms.IntegerField(label="Počet hodů kostkou", initial=0,
        validators=[MinValueValidator(0)])
    dotsCount = forms.IntegerField(label="Počet hozených bodů:", initial=0,
        validators=[MinValueValidator(0)])

    def __init__(self, allowedDices, *args, **kwargs):
        super(DiceThrowForm, self).__init__(*args, **kwargs)
        self.fields["dice"].choices = [(x, x.label) for x in allowedDices]
        self.fields["dice"].initial = self.fields["dice"].choices[0][0]
        if len(allowedDices) == 1:
            self.fields["dice"].widget = forms.HiddenInput()

class MoveInitialForm(forms.Form):
    team = captures("",
        TeamChoiceField(label="Tým"))
    action = captures("",
        EnumChoiceField(ActionType, label="Akce"))
    entity = forms.ChoiceField(required=False, label="Entita")
    canceled = forms.BooleanField(widget=forms.HiddenInput(), required=False, initial=False)

    def __init__(self, user, data=None, state=None, inherited=False, **kwargs):
        from game.models.actions import allowedActionTypes
        if data:
            super().__init__(data)
        else:
            super().__init__(**kwargs)

        self.helper = FormHelper()
        self.helper.form_tag = False

        if inherited and data is not None:
            self.fields["action"].choices = [(data["action"], "")]
            self.fields["entity"].choices = [(data["entity"], "")]
            self.commonLayout = Layout(
                Field('team'),
                Field('action'),
                Field('entity'),
                Field('canceled')
            )
            return

        allowedActions = allowedActionTypes(user)
        teams = Team.objects.all()
        self.allEntities = set()
        self.entityFilter = {}
        for action in Action.__subclasses__():
            if action.CiviMeta.move not in allowedActions:
                continue
            teamFilter = {}
            for team in teams:
                entities = action.relevantEntities(state, team)
                teamFilter[team] = set(entities)
                self.allEntities.update(entities)
            self.entityFilter[action] = teamFilter
        entities = list(dict.fromkeys(
            [(entity.id, entity.dropdownLabel) for entity in self.allEntities]))
        entities.sort(key=lambda x: x[1])
        self.fields["entity"].choices = [('', '-----------')] + entities
        self.fields["action"].choices = [('', '-----------')] + [(move.value, move.label) for move in allowedActions]
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
            super(MoveForm, self).__init__(data=data, user=user, state=state, inherited=True)
            self.entityId = data.get("entity")
        else:
            super(MoveForm, self).__init__(initial={
                    "action": action,
                    "team": team,
                    "entity": entity,
                }, state=state, user=user, inherited=True)
            self.entityId = entity
        for fieldName in ["action", "team", "entity"]:
            self.fields[fieldName].widget = forms.HiddenInput()

    def getEntity(self, entityType):
        if not self.entityId:
            raise InvalidActionException("Nezadali jste entitu.")
        try:
            return entityType.manager.latest().get(id=self.entityId)
        except entityType.DoesNotExist:
            raise InvalidActionException(f"Vámi zadaná entita s ID <i>{self.entityId}</i> neexistuje")



class AutoAdvanceForm(MoveForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper.layout = Layout(
            self.commonLayout,
            HTML(r"""
            <script>
                document.getElementsByTagName("FORM")[0].submit();
            </script>
            """)
        )