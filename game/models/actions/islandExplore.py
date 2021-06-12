from django import forms

from game.forms.action import MoveForm
from game.models.actionTypeList import ActionType
from game.models.actionBase import Action, ActionResult
from game.models.state import ResourceStorageAbstract
from game.data.entity import Direction
from django_enumfield.forms.fields import EnumChoiceField

DOTS_REQUIRED_MAX = 12
MAX_DISTANCE = 24

class IslandExploreForm(MoveForm):
    direction = EnumChoiceField(Direction, label="Směr")
    distance = forms.IntegerField(label="Vzdálenost", min_value=1, max_value=MAX_DISTANCE)

class IslandExploreMove(Action):
    class Meta:
        proxy = True
    class CiviMeta:
        move = ActionType.exploreIsland
        form = IslandExploreForm
        allowed = ["super", "org"]

    @staticmethod
    def relevantEntities(state, team):
        return []

    def requiresDice(self, state):
        return False

    # Just to ease accessing the arguments
    @property
    def distance(self):
        return self.arguments["distance"]

    @property
    def direction(self):
        return self.arguments["direction"]

    @staticmethod
    def build(data):
        action = IslandExploreMove(
            team=data["team"],
            move=data["action"],
            arguments=Action.stripData(data))
        return action

    def initiate(self, state):
        teamState = state.teamState(self.team)
        try:
            remainsToPay = teamState.resources.payResources(state.getPrice("islandExplorePrice"))
        except ResourceStorageAbstract.NotEnoughResourcesException as e:
            message = f'Nedostatek zdrojů; chybí: {self.costMessage(e.list)}'
            return ActionResult.makeFail(message)

        message = f"Tým musí zaplatit: {self.costMessage(remainsToPay)}"

        islands = filter(lambda x: x.isOnCoords(self.direction, self.distance), self.context.islands.all())
        islands = list(islands)
        if len(islands) == 0:
            message += "Po zaplacení týmu oznam, že na místě se nenachází žádný ostrov."
        else:
            island = islands[0]
            state.teamState(self.team).addExploredIsland(island.id)
            message += f"Po zaplacení týmu oznam, že úspěšně prozkoumali '{island.label}'."
        return ActionResult.makeSuccess(message)

    def commit(self, state):
        return ActionResult.makeSuccess()

    def abandon(self, state):
        return self.makeAbandon()

    def cancel(self, state):
        return self.makeCancel()