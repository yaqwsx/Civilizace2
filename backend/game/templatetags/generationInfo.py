from classytags.helpers import InclusionTag
from django import template
from django.utils import timezone
from game.models.generationTick import getExpectedGeneration

register = template.Library()

class GenerationInfo(InclusionTag):
    template = "game/tags/generationInfo.html"
    name = "generationInfo"

    def get_context(self, context):
        g = getExpectedGeneration()
        if g.generationDue:
            delta = g.generationDue - timezone.now()
            minutes, seconds = divmod(delta.seconds, 60)
        else:
            minutes, seconds = None, None
        return {
            "serverTime": timezone.now(),
            "remainsMin": minutes,
            "remainsSec": seconds,
            "generationSeq": g.seq,
            "generationDue": g.generationDue
        }

register.tag(GenerationInfo)