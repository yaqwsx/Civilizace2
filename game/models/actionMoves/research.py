from django import forms

from game.forms.action import MoveForm
from game.models.actionMovesList import ActionMove
from game.models.actionBase import Action, Dice

class ResearchForm(MoveForm):
    techId = forms.IntegerField(label="ID technologie:")
    techSelect = forms.ChoiceField(label="Vyber tech")

    def __init__(self, team, state, *args, **kwargs):
        super().__init__(team=team, state=state, *args, **kwargs)
        self.fields["techSelect"].choices = [
            ("tech-les", "Lesnictvi"),
            ("techbobule", "Bobule")]

class ResearchMove(Action):
    class Meta:
        proxy = True
    class CiviMeta:
        move = ActionMove.research
        form = ResearchForm
    def requiresDice(self):
        return True

    def dotsRequired(self):
        return { Dice.tech: 15, Dice.political: 24 }

    # Just to ease accessing the arguments
    @property
    def techId(self):
        return self.arguments["techId"]
    @techId.setter
    def techId(self, value):
        self.arguments["techId"] = value

    def sandbox(self, state):
        return self.teamState(state).sandbox

    @staticmethod
    def build(data):
        action = ResearchMove(team=data["team"], move=data["action"], arguments={})
        action.techId = data["techId"]
        return action

    def sane(self):
        # Just an example here
        return True

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

    def cancel(elf, state):
        return True, self.cancelMessage()