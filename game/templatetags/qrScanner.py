from classytags.helpers import InclusionTag
from django import template
from game.models.keywords import Keyword

register = template.Library()

class QrScanner(InclusionTag):
    template = "game/tags/qrScanner.html"
    name = "qrScanner"

    def get_context(self, context):
        return {
            "keywords": Keyword.objects.all()
        }

register.tag(QrScanner)