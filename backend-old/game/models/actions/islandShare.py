from django import forms

from game.models.users import Team
from game.forms.action import MoveForm, TeamChoiceField
from game.models.actionTypeList import ActionType
from game.models.actionBase import Action, ActionResult
from game.models.state import ResourceStorageAbstract
from game.data.entity import Direction, IslandModel
from django_enumfield.forms.fields import EnumChoiceField
from crispy_forms.layout import Layout, Fieldset, HTML

class IslandShareForm(MoveForm):
    recipient = TeamChoiceField(label="Komu")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        island = self.getEntity(IslandModel)
        self.fields["recipient"].label = f"Sdělit polohu {island.label} týmu"


class IslandShareMove(Action):
    class Meta:
        proxy = True
    class CiviMeta:
        move = ActionType.shareIsland
        form = IslandShareForm
        allowed = ["super", "org"]

    @staticmethod
    def relevantEntities(state, team):
        return state.teamState(team).exploredIslands

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
        action = IslandShareMove(
            team=data["team"],
            move=data["action"],
            arguments={
                "entity": data["entity"],
                "recipient": data["recipient"].pk
            })
        return action

    def initiate(self, state):
        if self.team == self.recipient:
            return ActionResult.makeFail("Není možné sdílet polohu ostrova sám se sebou")
        myTeamState = state.teamState(self.team)
        otherTeamState = state.teamState(self.recipient)

        if self.island not in myTeamState.exploredIslands:
            return ActionResult.makeFail("Není možné sdílet polohu ostrova, který tým nezná")
        if self.island in otherTeamState.exploredIslands:
            return ActionResult.makeFail("Není možné sdílet polohu ostrova, který přijímající tým už zná")

        otherTeamState.addExploredIsland(self.island.id)

        return ActionResult.makeSuccess(f"""
            Mapa {self.island.label} byla úspěšně nasdílena týmu {self.recipient.name}
        """)

    def commit(self, state):
        return ActionResult.makeSuccess()

    def abandon(self, state):
        return self.makeAbandon()

    def cancel(self, state):
        return self.makeCancel()