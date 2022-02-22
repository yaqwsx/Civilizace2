from django import forms

from game.forms.action import MoveForm
from game.models.actionTypeList import ActionType
from game.models.actionBase import Action, ActionResult, InvalidActionException
from game.data.entity import Direction, IslandModel
from game.data.resource import ResourceModel
from game.models.state import ResourceStorageAbstract
from django_enumfield.forms.fields import EnumChoiceField
from django.core.validators import MaxValueValidator, MinValueValidator
from crispy_forms.layout import Layout, Fieldset, HTML


class IslandAttackForm(MoveForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        island = self.getEntity(IslandModel)
        islandState = self.state.islandState(island)

        if islandState.owner.id == self.teamId:
            raise InvalidActionException("Nemůžete útočit na svůj vlastní otvor")

        if islandState.defense == 0:
            raise InvalidActionException(f"{island.label} má již nulovou obranu. Nelze účtočit.")

        price = self.state.getPrice("islandAttackPrice",
            len(self.state.teamIslands(self.teamId)) + 1)

        self.fields["diceThrow"] = forms.IntegerField(label="Počet hodů kostkou",
            validators=[MinValueValidator(1)])
        self.fields["success"] = forms.IntegerField(label="Kolik útoků se povedlo?",
            initial=0,
            validators=[MinValueValidator(0), MaxValueValidator(islandState.defense)])

        rows = [f'<li>{amount}× {res.htmlRepr()}</li>' for res, amount in price.items()]
        message = f"Vyberte od týmu: <ul>{''.join(rows)}</ul>"
        message += f"""
            <p>Následně budete s týmem házet útočnou kostkou. Každé 2 hody stojí tým
            1× {ResourceModel.manager.latest().get(id="mat-sila").htmlRepr()}.
            Zadejte počet hodů a to jestli tým souboj vyhrál.</p>
            """

        self.helper.layout = Layout(
            self.commonLayout,
            HTML(message),
            "diceThrow",
            "success"
        )

class IslandAttackMove(Action):
    class Meta:
        proxy = True
    class CiviMeta:
        move = ActionType.attackIsland
        form = IslandAttackForm
        allowed = ["super", "org"]

    @staticmethod
    def relevantEntities(state, team):
        teamIslands = [t.island.id for t in state.teamIslands(team)]
        return [t for t in state.teamState(team).exploredIslands if t.id not in teamIslands]

    def requiresDice(self, state):
        return False

    @staticmethod
    def build(data):
        action = IslandAttackMove(
            team=data["team"],
            move=data["action"],
            arguments=Action.stripData(data))
        return action

    @property
    def island(self):
        return self.context.islands.get(id=self.arguments["entity"])

    def initiate(self, state):
        teamState = state.teamState(self.team)
        islandState = state.islandState(self.island)

        if islandState.owner == self.team:
            return ActionResult.makeFail("Není možné útočit na vlastní ostrov")
        if islandState.defense == 0:
            return ActionResult.makeFail("Ostrov má již obranu na nule.")

        price = state.getPrice("islandAttackPrice",
            len(state.teamIslands(self.team)) + 1)
        price[ResourceModel.manager.latest().get(id="mat-sila")] = self.arguments["diceThrow"]

        try:
            remainsToPay = teamState.resources.payResources(price)
        except ResourceStorageAbstract.NotEnoughResourcesException as e:
            message = f'Nedostatek zdrojů; chybí: {self.costMessage(e.list)}'
            return ActionResult.makeFail(message)

        message = f"Tým musí zaplatit: {self.costMessage(remainsToPay)}"

        if self.arguments["success"]:
            islandState.defense -= self.arguments["success"]
            message += f"""
                Obrana {self.island.label} byla snížena na {islandState.defense}.
            """
        else:
            message += f"""
                Obrana {self.island.label} nebyla snížena.
                """
        return ActionResult.makeSuccess(message)


    def commit(self, state):
        return ActionResult.makeSuccess()

    def abandon(self, state):
        return self.makeAbandon()

    def cancel(self, state):
        return self.makeCancel()