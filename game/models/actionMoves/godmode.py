from crispy_forms.layout import Layout, Fieldset, Field, HTML

from django import forms

from game.forms.action import MoveForm
from game.models.actionBase import Action
from game.models.actionMovesList import ActionMove
from game.forms.layout import jsonDiffEditor

import json


class GodmodeForm(MoveForm):
    changes = forms.CharField(widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['changes'].initial = json.dumps({"add":[], "remove": [], "change": []})
        self.helper.layout = Layout(
            self.commonLayout, # Don't forget to add fields of the base form
            Field('changes'),
            jsonDiffEditor(self["changes"], self.state.toJson())
        )

class GodMove(Action):
    class Meta:
        proxy = True
    class CiviMeta:
        move = ActionMove.godmode
        form = GodmodeForm
        allowed = ["super"]

    @staticmethod
    def build(data):
        action = GodMove(
            team=data["team"],
            move=data["action"],
            arguments=json.loads(data["changes"])
        )
        return action

    @staticmethod
    def relevantEntities(state, team):
        return []

    def initiate(self, state):
        return True, ""

    def htmlList(self, dic):
        return "<ul class=\"list-disc px-6\">" + "".join([f"<li>{key}: {value}</li>" for key, value in dic.items()]) + "</ul>"

    def message(self):
        message = ""
        if self.arguments["add"]:
            message += "<b>Přidat:</b>" + self.htmlList(self.arguments["add"])
        if self.arguments["remove"]:
            message += "<b>Odebrat:</b>" + self.htmlList(self.arguments["remove"])
        if self.arguments["change"]:
            message += "<b>Změnit:</b>" + self.htmlList(self.arguments["change"])
        return message

    def commit(self, state):
        state.godUpdate(self.arguments)
        return True, self.message()

