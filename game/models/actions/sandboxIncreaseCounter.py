from django import forms

from game.forms.action import MoveForm
from game.models.actionTypeList import ActionType
from game.models.actionBase import Action, ActionResult
from game.data.entity import DieModel

class SanboxIncreaseCounterForm(MoveForm):
    amount = forms.IntegerField(label="Změna počítadla o:")

class SandboxIncreaseCounterMove(Action):
    class Meta:
        proxy = True
    class CiviMeta:
        move = ActionType.sanboxIncreaseCounter
        form = SanboxIncreaseCounterForm
        allowed = ["super"]

    @staticmethod
    def relevantEntities(state, team):
        return []

    def requiresDice(self, state):
        return True

    def dotsRequired(self, state):
        return { self.context.dies.get(id="die-plane"): 15, self.context.dies.get(id="die-hory"): 24 }

    # Just to ease accessing the arguments
    @property
    def amount(self):
        return self.arguments["amount"]

    @amount.setter
    def amount(self, value):
        self.arguments["amount"] = value

    def sandbox(self, state):
        return self.teamState(state).sandbox

    @staticmethod
    def build(data):
        action = SandboxIncreaseCounterMove(team=data["team"], move=data["action"], arguments={})
        action.amount = data["amount"]
        return action

    def initiate(self, state):
        val = self.sandbox(state).data["counter"] + self.amount
        if self.sandbox(state).data["counter"] >= 0:
            message = "Změní počítadlo na: {}".format(val)
            message += "<br>" + self.diceThrowMessage(state)
            return ActionResult.makeSuccess(message)
        message = "Počítadlo by kleslo pod nulu ({})".format(val)
        return ActionResult.makeFail(message)

    def commit(self, state):
        self.sandbox(state).data["counter"] += self.amount
        if self.sandbox(state).data["counter"] >= 0:
            message = "Počítadlo změněno na: {}. Řekni o tom týmu i Maarovi a vydej jim svačinu".format(self.sandbox(state).data["counter"])
            return ActionResult.makeSuccess(message)
        message = "Počítadlo by kleslo pod nulu ({})".format(self.sandbox(state).data["counter"])
        return ActionResult.makeFail(message)

    def abandon(self, state):
        return self.makeAbandon()

    def cancel(self, state):
        return self.makeCancel