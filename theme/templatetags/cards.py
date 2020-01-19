from classytags.core import Tag, Options
from classytags.arguments import Argument, MultiKeywordArgument
from classytags.helpers import InclusionTag
from django import template

register = template.Library()

class Card(InclusionTag):
    template = "tags/card.html"
    name = "card"
    options = Options(
        Argument("name"),
        MultiKeywordArgument("params", required=False, default= {
            "color": "green-600", "icon": "fa-wallet"}),
        blocks=[('endcard', 'nodelist')],
    )

    def get_context(self, context, name, params, nodelist):
        return {
            "cardContent": nodelist.render(context),
            "name": name,
            "params": params
        }

register.tag(Card)