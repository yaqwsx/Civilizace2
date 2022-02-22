from django import forms

from game.forms.action import MoveForm
from game.models.actionTypeList import ActionType
from game.models.actionBase import Action, ActionResult
from game.data.entity import EntityModel
from django_enumfield.forms.fields import EnumChoiceField
from game.models.stickers import Sticker, StickerType
from game.forms.action import AutoAdvanceForm

class InitialStickersForm(AutoAdvanceForm):
    pass

class InitialStickersMove(Action):
    class Meta:
        proxy = True
    class CiviMeta:
        move = ActionType.initialStickers
        form = InitialStickersForm
        allowed = ["super", "org"]

    @staticmethod
    def relevantEntities(state, team):
        return []

    def requiresDice(self, state):
        return False

    @staticmethod
    def build(data):
        action = InitialStickersMove(
            team=data["team"],
            move=data["action"], arguments=Action.stripData(data))
        return action

    def initiate(self, state):
        return ActionResult.makeSuccess("")

    def commit(self, state):
        tech = self.context.techs.get(id="build-centrum")
        result = ActionResult.makeSuccess("Týmu budou uděleny počáteční samolepky")

        result.addSticker(Sticker(entity=tech, type=StickerType.REGULAR))
        result.addSticker(Sticker(entity=tech, type=StickerType.COMPACT))
        for vyroba in tech.unlock_vyrobas.all():
            result.addSticker(Sticker(entity=vyroba, type=StickerType.REGULAR))

        return result
