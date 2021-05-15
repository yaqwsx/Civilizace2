from classytags.helpers import InclusionTag
from classytags.core import Options
from classytags.arguments import Argument
from django import template
from django.utils import timezone
from game.models.generationTick import getExpectedGeneration

register = template.Library()

class PrintStickersDialog(InclusionTag):
    template = "game/tags/printStickersDialog.html"
    name = "printStickersDialog"

    options = Options(
        Argument("dialogId")
    )

    def get_context(self, context, dialogId):
        return {
            "dialogId": dialogId
        }

register.tag(PrintStickersDialog)