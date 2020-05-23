from django import forms

from game.forms.action import MoveForm
from game.models.actionMovesList import ActionMove
from game.models.actionBase import Action, Dice

class SanboxIncreaseCounterForm(MoveForm):
    amount = forms.IntegerField(label="Změna počítadla o:")

class SandboxIncreaseCounterMove(Action):
    class Meta:
        proxy = True
    class CiviMeta:
        move = ActionMove.sanboxIncreaseCounter
        form = SanboxIncreaseCounterForm

    def requiresDice(self):
        return True

    def dotsRequired(self):
        return { Dice.tech: 15, Dice.political: 24 }

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

    def sane(self):
        # Just an example here
        return super.sane() and self.amount < 10000000

    def initiate(self, state):
        val = self.sandbox(state).data["counter"] + self.amount
        if self.sandbox(state).data["counter"] >= 0:
            message = "Změní počítadlo na: {}".format(val)
            message += "<br>" + self.diceThrowMessage()
            return True, message
        return False, "Počítadlo by kleslo pod nulu ({})".format(val)

    def commit(self, state):
        self.sandbox(state).data["counter"] += self.amount
        if self.sandbox(state).data["counter"] >= 0:
            message = "Počítadlo změněno na: {}. Řekni o tom týmu i Maarovi a vydej jim svačinu".format(self.sandbox(state).data["counter"])
            return True, message
        return False, "Počítadlo by kleslo pod nulu ({})".format(self.sandbox(state).data["counter"])

    def abandon(self, state):
        return True, self.abandonMessage()

    def cancel(self, state):
        return True, self.cancelMessage()