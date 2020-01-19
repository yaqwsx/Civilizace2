from .actionBase import Action, ActionMove
from game import forms

class CreateInitialMove(Action):
    class Meta:
        proxy = True
    class CiviMeta:
        move = ActionMove.createInitial
        form = None

class SandboxIncreaseCounterMove(Action):
    class Meta:
        proxy = True
    class CiviMeta:
        move = ActionMove.sanboxIncreaseCounter
        form = forms.SanboxIncreaseCounterForm

    # Just to ease accessing the arguments
    @property
    def amount(self):
        return self.arguments["amount"]
    @amount.setter
    def amount(self, value):
        self.arguments["amount"] = value

    def sandbox(self, state):
        return state.teamState(self.team.id).sandbox

    def build(data):
        action = SandboxIncreaseCounterMove(team=data["team"], move=data["action"], arguments={})
        action.amount = data["amount"]
        return action

    def sane(self):
        # Just an example here
        return super.sane() and self.amount < 10000000

    def effect(self, state):
        val = self.sandbox(state).data["counter"] + self.amount
        if val >= 0:
            message = "Změní počítadlo na: {}. Řekni o tom týmu i Maarovi a vydej jim svačinu".format(val)
            return True, message
        return False, "Počítadlo by kleslo pod nulu ({})".format(val)

    def applyTo(self, state):
        self.sandbox(state).data["counter"] += self.amount