from django import forms

from game.forms.action import MoveForm
from game.models.actionTypeList import ActionType
from game.models.actionBase import Action, ActionResult, InvalidActionException
from game.data.entity import Direction, IslandModel
from game.data.resource import ResourceModel
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
        self.fields["success"] = forms.ChoiceField(label="Povedl se útok?",
            choices=[(False, "Ne"), (True, "Ano")])

        rows = [f'<li>{amount}× {res.htmlRepr()}</li>' for res, amount in price.items()]
        message = f"Vyberte od týmu: <ul>{''.join(rows)}</ul>"
        message += f"""
            <p>Následně budete s týmem házet útočnou kostkou. Každý hod stojí tým
            1× {ResourceModel.manager.latest().get(id="lod-sila").htmlRepr()}.
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

    def initiate(self, state):
        raise NotImplementedError("Honza will implement this...")

    def commit(self, state):
        return ActionResult.makeSuccess()

    def abandon(self, state):
        return self.makeAbandon()

    def cancel(self, state):
        return self.makeCancel()