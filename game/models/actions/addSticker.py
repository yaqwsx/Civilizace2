from django import forms

from game.forms.action import MoveForm
from game.models.actionTypeList import ActionType
from game.models.actionBase import Action, ActionResult
from game.data.entity import EntityModel
from game.models.stickers import Sticker

class AddStickerForm(MoveForm):
    def __init__(self, *arg, **kwarg):
        super().__init__(*arg, **kwarg)
        self.getEntity(EntityModel)

class AddStickerMove(Action):
    class Meta:
        proxy = True
    class CiviMeta:
        move = ActionType.addSticker
        form = AddStickerForm
        allowed = ["super"]

    @staticmethod
    def relevantEntities(state, team):
        return state.context.entities.all()

    def requiresDice(self, state):
        return False

    @staticmethod
    def build(data):
        action = AddStickerMove(
            team=data["team"],
            move=data["action"], arguments=Action.stripData(data))
        return action

    def initiate(self, state):
        return ActionResult.makeSuccess("")


    def commit(self, state):
        result = ActionResult.makeSuccess("Akce se povedla")
        # result.stickers.append(Sti)
        return result
