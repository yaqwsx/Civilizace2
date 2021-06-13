from django import forms
from django.db.models.query import InstanceCheckMeta

from game.forms.action import MoveForm
from game.models.actionTypeList import ActionType
from game.models.actionBase import Action, ActionResult
from game.models.state import ResourceStorageAbstract
from game.data.entity import Direction, IslandModel
from django_enumfield.forms.fields import EnumChoiceField
from django.core.validators import MaxValueValidator, MinValueValidator


class IslandRepairForm(MoveForm):
    number = forms.IntegerField(label="Počet věží k opravě", min_value=0)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        island = self.getEntity(IslandModel)
        islandState = self.state.islandState(island)
        self.fields["number"].validators = [
            MinValueValidator(0),
            MaxValueValidator(islandState.maxDefense - islandState.defense)
        ]

class IslandRepairMove(Action):
    class Meta:
        proxy = True
    class CiviMeta:
        move = ActionType.repairIsland
        form = IslandRepairForm
        allowed = ["super", "org"]

    @staticmethod
    def relevantEntities(state, team):
        return [i.island for i in state.teamIslands(team)]

    def requiresDice(self, state):
        return False

    # Just to ease accessing the arguments
    @property
    def island(self):
        return self.context.islands.get(id=self.arguments["entity"])

    @property
    def number(self):
        return self.arguments["number"]

    @staticmethod
    def build(data):
        action = IslandRepairMove(
            team=data["team"],
            move=data["action"],
            arguments=Action.stripData(data))
        return action

    def initiate(self, state):
        teamState = state.teamState(self.team)
        islandState = state.islandState(self.island)

        if islandState.owner != self.team:
            return ActionResult.makeFail("Není možné opravovat ostrov, který týmu nepatří")
        if islandState.defense + self.number > islandState.maxDefense:
            return ActionResult.makeFail(f"{self.number} je příliš mnoho věží. Ostrov jich nemůže mít tolik")

        try:
            remainsToPay = teamState.resources.payResources(
                state.getPrice("islandRepairPrice", self.number))
        except ResourceStorageAbstract.NotEnoughResourcesException as e:
            message = f'Nedostatek zdrojů; chybí: {self.costMessage(e.list)}'
            return ActionResult.makeFail(message)

        islandState.defense += self.number

        message = f"Tým musí zaplatit: {self.costMessage(remainsToPay)}"

        message += f"<br/>Opevnění ostrova bylo opraveno. {self.island.label} má nyní opevnění {islandState.defense}"
        return ActionResult.makeSuccess(message)

    def commit(self, state):
        return ActionResult.makeSuccess()

    def abandon(self, state):
        return self.makeAbandon()

    def cancel(self, state):
        return self.makeCancel()