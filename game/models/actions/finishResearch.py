from game.data.task import AssignedTask
from django import forms
from crispy_forms.layout import Layout, Fieldset, HTML

from game.data.tech import TechEdgeModel, TechModel
from game.data.entity import DieModel
from game.forms.action import MoveForm
from game.models.actionTypeList import ActionType
from game.models.actionBase import Action, InvalidActionException, ActionResult
from game.models.state import TechStatusEnum
from game.models.stickers import StickerType, Sticker


class FinishResearchForm(MoveForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        tech = self.getEntity(TechModel)
        try:
            assignment = AssignedTask.objects.get(
                techId=tech.id,
                team=self.teamId,
            )
            message = f"""Zkontrolujte, že tým dokončil úkol '{assignment.task.name}'"""
        except AssignedTask.DoesNotExist:
            message = "Tým nemusel splnit žádný úkol, pokračujte."
        self.helper.layout = Layout(
            self.commonLayout,
            HTML(message)
        )

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
        return ActionResult.makeSuccess()

    def commit(self, state):
        tech = self.context.techs.get(id=self.arguments["entity"])
        techs = self.teamState(state).techs
        try:
            assignment = AssignedTask.objects.get(
                techId=tech.id,
                team=self.team,
            )
        except AssignedTask.DoesNotExist:
            assignment = None

        status = techs.getStatus(tech)
        if status == TechStatusEnum.OWNED:
            return ActionResult.makeFail(f'Technologii {tech.label} nelze dozkoumat, tým ji již vlastní')
        if status == TechStatusEnum.UNKNOWN:
            return ActionResult.makeFail(f'Technologii {tech.label} nelze dozkoumat, jelikož se ještě nezačala zkoumat')
        techs.setStatus(tech, TechStatusEnum.OWNED)

        result = ActionResult.makeSuccess(f"""Technologie {tech.label} bude dozkoumána.""")
        if assignment:
            result.finishTask(assignment.task)
        result.addSticker(Sticker(entity=tech, type=StickerType.REGULAR))
        for vyroba in tech.unlock_vyrobas.all():
            result.addSticker(Sticker(entity=vyroba, type=StickerType.REGULAR))
        return result
