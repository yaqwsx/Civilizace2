from game.forms.action import MoveForm
from game.models.actionMovesList import ActionMove
from game.models.actionBase import Action

class CreateInitialForm(MoveForm):
    pass

class CreateInitialMove(Action):
    class Meta:
        proxy = True
    class CiviMeta:
        move = ActionMove.createInitial
        form = CreateInitialForm
        allowed = []

    @staticmethod
    def relevantEntities(state, team):
        return []
