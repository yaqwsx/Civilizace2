from game import forms
from game.models import Action, ActionMove


class NextTurn(Action):
    class Meta:
        proxy = True
    class CiviMeta:
        move = ActionMove.nextTurn
        form = forms.NextTurnForm

    def build(data):
        action = NextTurn(team=data["team"], move=data["action"], arguments={})
        return action

    def commit(self, state):
        team = self.teamState(state)
        team.nextTurn()
        message = """Začalo kolo {turn}""".format(turn=team.turn)
        return True, message


