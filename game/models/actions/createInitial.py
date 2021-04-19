from game.forms.action import MoveForm
from game.models.actionTypeList import ActionType
from game.models.actionBase import Action

class CreateInitialForm(MoveForm):
    pass

class CreateInitialMove(Action):
    class Meta:
        proxy = True
    class CiviMeta:
        move = ActionType.createInitial
        form = CreateInitialForm
        allowed = []

    @staticmethod
    def relevantEntities(state, team):
        return []
