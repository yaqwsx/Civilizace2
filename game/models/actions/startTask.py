from django import forms

from game.forms.action import MoveForm
from game.models.actionTypeList import ActionType
from game.models.actionBase import Action, ActionResult
from game.data.entity import TaskModel

class StartTaskForm(MoveForm):
    def __init__(self, *arg, **kwarg):
        super().__init__(*arg, **kwarg)
        self.getEntity(TaskModel)

class StartTaskMove(Action):
    class Meta:
        proxy = True
    class CiviMeta:
        move = ActionType.startTask
        form = StartTaskForm
        allowed = ["super"]

    @property
    def entity(self):
        return TaskModel.objects.get(pk=self.arguments["entity"])

    @staticmethod
    def relevantEntities(state, team):
        allTasks = TaskModel.objects.all()
        assignedTasks = team.assignedTasks.all()
        return allTasks.difference(assignedTasks)

    def requiresDice(self, state):
        return False

    @staticmethod
    def build(data):
        action = StartTaskMove(
            team=data["team"],
            move=data["action"], arguments=Action.stripData(data))
        return action

    def initiate(self, state):
        return ActionResult.makeSuccess("")

    def commit(self, state):
        result = ActionResult.makeSuccess("Akce se povedla")
        result.startTask(self.entity, None)
        return result
