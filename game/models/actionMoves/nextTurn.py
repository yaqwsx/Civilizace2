import math

from game.data import ResourceModel
from game.forms.action import MoveForm
from game.models.actionMovesList import ActionMove
from game.models.actionBase import Action, InvalidActionException


class NextTurnForm(MoveForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        generation = self.state.worldState.generation
        turn = self.state.teamState(self.teamId).turn

        if turn >= generation:
            raise InvalidActionException("Tým už v této generaci kolo začal")

class NextTurn(Action):
    class Meta:
        proxy = True
    class CiviMeta:
        move = ActionMove.nextTurn
        form = NextTurnForm

    @staticmethod
    def relevantEntities(state, team):
        return []

    def build(data):
        action = NextTurn(team=data["team"], move=data["action"], arguments={})
        return action

    def initiate(self, state):
        return True, "Začíná kolo!"

    def commit(self, state):
        team = self.teamState(state)

        storage = team.resources

        # obyvatele a prace
        praceLeft = storage.getAmount("res-prace")
        obyvatele = storage.getAmount("res-obyvatel")

        prace = obyvatele + math.floor(praceLeft/2)
        print("prace: " + str(prace))
        storage.setAmount("res-prace", prace)

        team.nextTurn()
        message = """Začalo kolo {turn}""".format(turn=team.turn)
        return True, message

