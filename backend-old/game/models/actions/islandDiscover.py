from django import forms

from game.forms.action import MoveForm
from game.models.actionTypeList import ActionType
from game.models.actionBase import Action, ActionResult
from game.data.entity import Direction
from django_enumfield.forms.fields import EnumChoiceField

DOTS_REQUIRED_MAX = 12
MAX_DISTANCE = 24

class IslandDiscoverForm(MoveForm):
    direction = EnumChoiceField(Direction, label="Směr")
    distance = forms.IntegerField(label="Vzdálenost", min_value=0, max_value=MAX_DISTANCE)

class IslandDiscoverMove(Action):
    class Meta:
        proxy = True
    class CiviMeta:
        move = ActionType.discoverIsland
        form = IslandDiscoverForm
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
        action = IslandDiscoverMove(
            team=data["team"],
            move=data["action"],
            arguments=Action.stripData(data))
        return action

    def initiate(self, state):
        dotsRequired = max(1, int(self.distance * DOTS_REQUIRED_MAX / MAX_DISTANCE ))
        islands = filter(lambda x: x.isOnCoords(self.direction, self.distance), self.context.islands.all())
        islands = list(islands)
        if len(islands) > 0:
            state.teamState(self.team).addDiscoveredIsland(islands[0].id)
        die = self.context.dies.get(id=self.direction.correspondingDie)
        message = f"Vyzvi tým k tomu, aby hodil kostkou '{die.label}'. "
        message += f"Na zadaném políčku se " + ("✓ nachází" if len(islands) > 0 else "<b>✘ NE</b>nachází") + " ostrov."
        message += f"Tuto informaci týmu sděl pouze pokud hodí <b>aslespoň {dotsRequired}</b>."

        return ActionResult.makeSuccess(message)

    def commit(self, state):
        return ActionResult.makeSuccess()

    def abandon(self, state):
        return self.makeAbandon()

    def cancel(self, state):
        return self.makeCancel()