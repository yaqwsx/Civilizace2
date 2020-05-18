from game.forms.action import MoveForm
from game.models.actionMovesList import ActionMove
from game.models.actionBase import Action


class NextTurnForm(MoveForm):
    pass

class NextTurn(Action):
    class Meta:
        proxy = True
    class CiviMeta:
        move = ActionMove.nextTurn
        form = NextTurnForm

    def build(data):
        action = NextTurn(team=data["team"], move=data["action"], arguments={})
        return action

    def commit(self, state):
        team = self.teamState(state)
        team.nextTurn()
        message = """Začalo kolo {turn}""".format(turn=team.turn)
        return True, message


