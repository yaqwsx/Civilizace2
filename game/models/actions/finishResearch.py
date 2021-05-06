from django import forms
from crispy_forms.layout import Layout, Fieldset, HTML

from game.data.tech import TechEdgeModel, TechModel
from game.data.entity import DieModel
from game.forms.action import MoveForm
from game.models.actionTypeList import ActionType
from game.models.actionBase import Action, InvalidActionException
from game.models.state import TechStorageItem, TechStatusEnum


class FinishResearchForm(MoveForm):
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

class FinishResearchMove(Action):
    class Meta:
        proxy = True
    class CiviMeta:
        move = ActionType.finishResearch
        form = FinishResearchForm
        allowed = ["super", "org"]

    @staticmethod
    def build(data):
        action = FinishResearchMove(
            team=data["team"],
            move=data["action"],
            arguments=Action.stripData(data))
        return action

    @staticmethod
    def relevantEntities(state, team):
        techs = state.teamState(team.id).techs
        return techs.getTechsUnderResearch()

    def requiresDice(self, state):
        return False

    def initiate(self, state):
        return True, ""

    def commit(self, state):
        tech = self.context.techs.get(id=self.arguments["entity"])
        techs = self.teamState(state).techs
        status = techs.getStatus(tech)
        if status == TechStatusEnum.OWNED:
            return False, f'Technologii {tech.label} nelze dozkoumat, tým ji již vlastní'
        if status == TechStatusEnum.UNKNOWN:
            return False, f'Technologii {tech.label} nelze dozkoumat, jelikož se ještě nezačala zkoumat'
        techs.setStatus(tech, TechStatusEnum.OWNED)
        stickers = [tech.label] + \
            [f'Výroba: <i>{x.label}</i>' for x in tech.unlock_vyrobas.all()] + \
            [f'Vylepšeni: <i>{x.label}</i>' for x in tech.unlock_enhancers.all()]
        stickerMsg = "".join([f'<li>{x}</li>' for x in stickers])
        return True, f"""Technologie {tech.label} bude dozkoumána.<br><br>
                    {tech.task.htmlRepr()}<br><br>
                    Vydej týmu následující samolepky:
                    <ul class="list-disc px-4">{stickerMsg}</ul>"""
