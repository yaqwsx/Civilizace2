from game.models.state import IslandState
from game.forms.action import MoveForm, AutoAdvanceForm
from game.models.actionTypeList import ActionType
from game.models.actionBase import Action, ActionResult

class EnsureEntityStatesForm(AutoAdvanceForm):
    pass

class EnsureEntityStatesMove(Action):
    class Meta:
        proxy = True
    class CiviMeta:
        move = ActionType.ensureEntitiyState
        form = EnsureEntityStatesForm
        allowed = ["super"]

    @staticmethod
    def build(data):
        action = EnsureEntityStatesMove(team=data["team"], move=data["action"], arguments=Action.stripData(data))
        return action

    @staticmethod
    def relevantEntities(state, team):
        return []

    def requiresDice(self, state):
        return False

    def initiate(self, state):
        return ActionResult.makeSuccess("")

    def commit(self, state):
        items = []
        for island in state.context.islands.all():
            if state.islandStates.filter(islandId=island.id).exists():
                continue
            iss = IslandState.objects.createInitial(islandId=island.id, context=state.context)
            state.islandStates.add(iss)
            items.append(f"Adding state for island {island.id}")
        if len(items) == 0:
            message = "Nic nepřidáno"
        else:
            message = "<ul>" + "\n".join([f"<li>{x}</li>" for x in items]) + "</ul>"
        return ActionResult.makeSuccess(message)
