import math
from crispy_forms.layout import Layout, Fieldset, HTML

from django import forms
from django.core.validators import MinValueValidator, MaxValueValidator

from game.data import ResourceModel
from game.forms.action import MoveForm
from game.models.actionBase import Action
from game.models.actionMovesList import ActionMove
from game.models.users import Team


class TradeForm(MoveForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        team = self.state.teamState(self.teamId)
        resources = team.resources.getResourcesByType()
        print("Available productions: " + str(resources))

        layoutData = [self.commonLayout]

        choices = []
        for them in filter(
            lambda them: them.id != self.teamId,
            Team.objects.all()
        ):
            distance = team.distances.getTeamDistance(them)
            choices.append((them.id, f"{them.name} (vzdálenost {distance})"))
        self.fields["thatTeamField"] = forms.ChoiceField(
            label=f"Adresát",
            choices = choices
        )
        layoutData.append(Fieldset("", "thatTeamField"))

        fields = [f"Máte k dispozici {team.resources.getAmount('res-nosic')} obchodníků"]

        for resource, amount in resources.items():
            self.fields[resource.id] = forms.IntegerField(
                label=f"{resource.htmlRepr()} (max. {amount}x)",
                validators=[MinValueValidator(0), MaxValueValidator(amount)],
                initial=0)
            fields.append(resource.id)

        layoutData.append(Fieldset(*fields))
        self.helper.layout = Layout(*layoutData)

class TradeMove(Action):
    class Meta:
        proxy = True
    class CiviMeta:
        move = ActionMove.trade
        form = TradeForm
        allowed = ["super", "org"]

    @staticmethod
    def build(data):
        action = TradeMove(
            team=data["team"],
            move=data["action"],
            arguments={**data})
        return action

    @staticmethod
    def relevantEntities(state, team):
        return []

    def initiate(self, state):
        team = self.teamState(state)
        themTeam = Team.objects.get(id=self.arguments["thatTeamField"])
        them = state.teamState(themTeam)
        message = ["Produkce byly přesměrovány"]

        resources = {}
        vliv = 0
        volume = 0

        for key in filter(lambda x: x[:5] == "prod-", self.arguments.keys()):
            if not self.arguments[key]:
                continue
            resource = ResourceModel.objects.get(id=key)
            amount = self.arguments[key]
            resources[resource] = amount
            message.append(f"  {amount}x {resource.htmlRepr()}")

            level = resource.level
            vliv += level*amount
            volume += amount

        team.resources.payResources(resources)
        them.resources.receiveResources(resources)
        team.vliv.addVliv(themTeam, vliv)

        distance = team.distances.getTeamDistance(themTeam)
        requiredTrade = distance * volume

        availableTrade = team.resources.getAmount("res-nosic")
        print("availableTrade: " + str(availableTrade))
        message.append(f"K provedení obchodu je potřeba {requiredTrade} nosičů")

        if availableTrade < requiredTrade:
            traderActions = math.ceil((requiredTrade-availableTrade) / 20)
            team.resources.payResources({ResourceModel.objects.get(id="res-obyvatel"): traderActions*2})
            team.resources.receiveResources({ResourceModel.objects.get(id="res-nosic"): traderActions*20})
            availableTrade = team.resources.getAmount("res-nosic")
            print("availableTrade: " + str(availableTrade))
            message.append(f"Bylo vyrobeno {traderActions*20} nosičů (cena: <b>{traderActions*2}x {ResourceModel.objects.get(id='res-obyvatel').htmlRepr()}</b>)")

        team.resources.payResources({ResourceModel.objects.get(id="res-nosic"): requiredTrade})

        self.arguments["team"] = None
        return True, "<br>".join(message)

    def commit(self, state):
        return True, ""
