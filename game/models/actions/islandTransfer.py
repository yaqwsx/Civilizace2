from django import forms

from game.models.users import Team
from game.forms.action import MoveForm, TeamChoiceField
from game.models.actionTypeList import ActionType
from game.models.actionBase import Action, ActionResult
from game.models.state import ResourceStorageAbstract
from game.data.entity import Direction, IslandModel
from django_enumfield.forms.fields import EnumChoiceField
from crispy_forms.layout import Layout, Fieldset, HTML

class IslandTransferForm(MoveForm):
    recipient = TeamChoiceField(label="Komu")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        island = self.getEntity(IslandModel)
        self.fields["recipient"].label = f"Předat ostrov {island.label} týmu"


class IslandTransferMove(Action):
    class Meta:
        proxy = True
    class CiviMeta:
        move = ActionType.transferIsland
        form = IslandTransferForm
        allowed = ["super", "org"]

    @staticmethod
    def relevantEntities(state, team):
        return [i.island for i in state.teamIslands(team)]

    def requiresDice(self, state):
        return False

    # Just to ease accessing the arguments
    @property
    def recipient(self):
        return Team.objects.get(pk=self.arguments["recipient"])

    @property
    def island(self):
        return self.context.islands.get(id=self.arguments["entity"])


    @staticmethod
    def build(data):
        action = IslandTransferMove(
            team=data["team"],
            move=data["action"],
            arguments={
                "entity": data["entity"],
                "recipient": data["recipient"].pk
            })
        return action

    def price(self, state):
        teamIslands = state.teamIslands(self.recipient)
        return state.getPrice("islandColonizePrice", len(teamIslands) + 1)

    def initiate(self, state):
        if self.team == self.recipient:
            return ActionResult.makeFail("Není možné předat ostrov sám se sobě")
        islandState = state.islandState(self.island)

        if islandState.owner != self.team:
            return ActionResult.makeFail("Není možné sdílet předat ostrov, který tým nevlastní")

        price = self.price(state)
        recipientState = state.teamState(self.recipient)
        try:
            remainsToPay = recipientState.resources.payResources(price)
        except ResourceStorageAbstract.NotEnoughResourcesException as e:
            message = f'Nemohu předat ostrov {self.island.label} - tým {self.recipient.name} nedostatek zdrojů; chybí: {self.costMessage(e.list)}'
            return ActionResult.makeFail(message)

        message = f"""
            Tým <b>{self.recipient.name}</b> musí zaplatit: {self.costMessage(remainsToPay)}</br>

            Mapa {self.island.label} byla úspěšně nasdílena týmu {self.recipient.name}
            """

        islandState.owner = self.recipient

        return ActionResult.makeSuccess(message)

    def commit(self, state):
        return ActionResult.makeSuccess()

    def abandon(self, state):
        return self.makeAbandon()

    def cancel(self, state):
        return self.makeCancel()