from django import forms

from game.forms.action import MoveForm
from game.models.actionTypeList import ActionType
from game.models.actionBase import Action, ActionResult
from game.data.entity import TaskModel

class FinishTaskForm(MoveForm):
    def __init__(self, *arg, **kwarg):
        super().__init__(*arg, **kwarg)
        self.getEntity(TaskModel)

class FinishTaskMove(Action):
    class Meta:
        proxy = True
    class CiviMeta:
        move = ActionType.finishTask
        form = FinishTaskForm
        allowed = ["super"]

    @property
    def entity(self):
        return TaskModel.objects.get(id=self.arguments["entity"])

    @staticmethod
    def relevantEntities(state, team):
        return team.assignedTasks.all()

    def requiresDice(self, state):
        return False

    @staticmethod
    def build(data):
        action = FinishTaskMove(
            team=data["team"],
            move=data["action"], arguments=Action.stripData(data))
        return action

    def initiate(self, state):
        return ActionResult.makeSuccess("")

    def commit(self, state):
        result = ActionResult.makeSuccess("Akce se povedla")
        result.finishTask(self.entity)
        return result
