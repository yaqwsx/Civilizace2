from classytags.helpers import InclusionTag
from django import template

register = template.Library()

class QrScanner(InclusionTag):
    template = "game/tags/qrScanner.html"
    name = "qrScanner"

    def get_context(self, context):
        return {}

register.tag(QrScanner)