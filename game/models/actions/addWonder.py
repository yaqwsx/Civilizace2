from django import forms
from crispy_forms.layout import Layout, Fieldset, HTML

from game.data.tech import TechEdgeModel, TechModel
from game.data.entity import DieModel
from game.forms.action import MoveForm
from game.models.actionTypeList import ActionType
from game.models.actionBase import Action, InvalidActionException
from game.models.state import TechStatusEnum


class AddWonderForm(MoveForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper.layout = Layout(
            self.commonLayout,
            HTML(r"""
            <script>
                document.getElementsByTagName("FORM")[0].submit();
            </script>
            """)
        )
        self.getEntity(TechModel)

class AddWonderMove(Action):
    class Meta:
        proxy = True
    class CiviMeta:
        move = ActionType.addWonder
        form = AddWonderForm
        allowed = ["super", "org"]

    @staticmethod
    def build(data):
        action = AddWonderMove(
            team=data["team"],
            move=data["action"],
            arguments=Action.stripData(data))
        return action

    @staticmethod
    def relevantEntities(state, team):
        techs = state.teamState(team.id).techs
        return TechModel.manager.latest().filter(id__startswith="div-zaklad")

    def requiresDice(self, state):
        return False

    def initiate(self, state):
        return True, ""

    def commit(self, state):
        tech = self.context.techs.get(id=self.arguments["entity"])
        techs = self.teamState(state).techs
        status = techs.getStatus(tech)
        if status == TechStatusEnum.OWNED:
            return False, f'Div {tech.label} nelze přidat, tým ho již vlastní'
        techs.setStatus(tech, TechStatusEnum.RESEARCHING)
        return True, f'Div {tech.label} bude přidán týmu. Dejte mu příslušnou samolepku'
