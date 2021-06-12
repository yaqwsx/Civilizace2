from django import forms
from crispy_forms.layout import Layout, Fieldset, HTML

from game.forms.action import MoveForm
from game.models.actionTypeList import ActionType
from game.models.actionBase import Action, ActionResult
from game.models.state import ResourceStorageAbstract
from game.data.entity import Direction, IslandModel
from django_enumfield.forms.fields import EnumChoiceField

DOTS_REQUIRED_MAX = 12
MAX_DISTANCE = 24

class IslandColonizeForm(MoveForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper.layout = Layout(
            self.commonLayout,
            HTML(r"""
            <script>
                document.getElementsByTagName("FORM")[0].submit();
            </script>
            """)
        )
        self.getEntity(IslandModel)

class IslandColonizeMove(Action):
    class Meta:
        proxy = True
    class CiviMeta:
        move = ActionType.colonizeIsland
        form = IslandColonizeForm
        allowed = ["super", "org"]

    @staticmethod
    def relevantEntities(state, team):
        teamState = state.teamState(team)
        owned = [x.island.id for x in state.teamIslands(team)]
        return [x for x in teamState.exploredIslands if x not in owned]

    def requiresDice(self, state):
        return True

    def dotsRequired(self, state):
        teamIslands = state.teamIslands(self.team)
        return {
            self.context.dies.get(id="die-any"):
                state.parameters["islandColonizeDots"] * (len(teamIslands) + 1)}

    @staticmethod
    def build(data):
        action = IslandColonizeMove(
            team=data["team"],
            move=data["action"],
            arguments=Action.stripData(data))
        return action

    @property
    def island(self):
        return self.context.islands.get(id=self.arguments["entity"])

    def price(self, state):
        teamIslands = state.teamIslands(self.team)
        return state.getPrice("islandColonizePrice", len(teamIslands) + 1)

    def initiate(self, state):
        islandState = state.islandState(self.island)
        teamState = state.teamState(self.team)
        if islandState.island.id not in teamState.exploredIslandsList:
                return ActionResult.makeFail(f"Tým nezná {self.island.label}. Není možné kolonizovat.")
        if islandState.defense != 0:
            return ActionResult.makeFail(f"Ostrov {self.island.label} má nenulovou obranu. Není možné kolonizovat.")
        price = self.price(state)
        try:
            remainsToPay = teamState.resources.payResources(price)
        except ResourceStorageAbstract.NotEnoughResourcesException as e:
            message = f'Nemohu kolonizovat {self.island.label} - nedostatek zdrojů; chybí: {self.costMessage(e.list)}'
            return ActionResult.makeFail(message)

        message = f"Pro kolonizaci {self.island.label} "
        message += f"je třeba zaplatit: {self.costMessage(remainsToPay)} a hodit: "
        message += self.diceThrowMessage(state)
        return ActionResult.makeSuccess(message)

    def commit(self, state):
        islandState = state.islandState(self.island)
        previous = islandState.owner
        islandState.owner = self.team
        message = f"Týmu se podařilo kolonizovat {islandState.island.label}."
        if previous is None:
            message += "Vydej týmu příslušnou kartu ostrova."
        else:
            message += f"Kartu ostrova mají {previous.name}, pošli tým za nimi, aby si převzal kartu ostrova"
        return ActionResult.makeSuccess(message)

    def abandon(self, state):
        return self.makeAbandon()

    def cancel(self, state):
        price = self.price(state)
        teamState =  state.teamState(self.team)
        materials = teamState.resources.returnResources(price)
        message = f"Vraťte týmu materiály: {self.costMessage(materials)}"
        return self.makeCancel(message)