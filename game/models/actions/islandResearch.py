from django import forms

from game.data.tech import TechEdgeModel, TechModel
from game.data.entity import DieModel
from game.forms.action import MoveForm
from game.models.actionTypeList import ActionType
from game.models.actionBase import Action, InvalidActionException, ActionResult
from game.models.state import TechStatusEnum, ResourceStorage


class IslandResearchForm(MoveForm):
    techSelect = forms.ChoiceField(label="Vyber výzkum")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        src = self.getEntity(TechModel)
        island = src.island
        islandState = self.state.islandState(island)
        if islandState.owner.id != self.teamId:
            raise InvalidActionException("Tady už není co zkoumat (" + src.label + ")")

        techs = islandState.techs
        choices = []
        for edge in src.unlocks_tech.all():
            if techs.getStatus(edge.dst) == TechStatusEnum.UNKNOWN:
                choices.append((edge.id, edge.label))
        if not len(choices):
            raise InvalidActionException("Tady už není co zkoumat (" + src.label + ")")
        self.fields["techSelect"].choices = choices

class IslandResearchMove(Action):
    class Meta:
        proxy = True
    class CiviMeta:
        move = ActionType.researchIsland
        form = IslandResearchForm
        allowed = ["super", "org"]

    @staticmethod
    def build(data):
        action = IslandResearchMove(
            team=data["team"],
            move=data["action"],
            arguments=Action.stripData(data))
        return action

    @staticmethod
    def relevantEntities(state, team):
        teamIslands = state.teamIslands(team)
        techs = []
        for i in teamIslands:
            techs.extend(i.techs.getOwnedTechs())
        return techs

    @property
    def edge(self):
        return self.context.edges.get(id=self.arguments["techSelect"])

    def requiresDice(self, state):
        return True

    def dotsRequired(self, state):
        return {self.edge.die: self.edge.dots}

    def initiate(self, state):
        teamState = self.teamState(state)
        island = self.edge.src.island
        islandState = state.islandState(island)
        techs = islandState.techs

        dst = self.edge.dst

        if techs.getStatus(self.edge.src) != TechStatusEnum.OWNED:
            return ActionResult.makeFail(f"Zdrojová technologie {self.edge.src.label} není vyzkoumána.")
        dstStatus = techs.getStatus(dst)
        if dstStatus == TechStatusEnum.OWNED:
            return ActionResult.makeFail(f"Cílová technologie {dst.label} už byla kompletně vyzkoumána.")
        if dstStatus == TechStatusEnum.RESEARCHING:
            return ActionResult.makeFail(f"Cilová technologie {dst.label} už je zkoumána.")

        try:
            print(self.edge.getInputs())
            materials = teamState.resources.payResources(self.edge.getInputs())
            if materials:
                costMessage = f'Tým musí zaplatit: {self.costMessage(materials)}>'
            else:
                costMessage = "Tým nic neplatí"
        except ResourceStorage.NotEnoughResourcesException as e:
            message = f'Nedostate zdrojů; chybí: {self.costMessage(e.list)}'
            return ActionResult.makeFail(message)
        return ActionResult.makeSuccess(
            f"""
                Pro vyzkoumání <i>{self.edge.dst.label}</i> skrze <i>{self.edge.label}</i> je třeba hodit: {self.edge.dots}&times; {self.edge.die.label}<br>
                {costMessage}<br>
            """)

    def commit(self, state):
        dst = self.edge.dst
        island = dst.island
        islandState = state.islandState(island)
        islandState.techs.setStatus(dst, TechStatusEnum.OWNED)
        message = f"Technologie {dst.label} na ostrově {island.label} byla vyzkoumána."
        if dst.defenseBonus:
            islandState.defense += dst.defenseBonus
            message += f"""<br/>
                Maximální hodnota ostrova {island.label} byla zvýšena na
                {islandState.maxDefense}. Aktuální obrana je {islandState.defense}.
            """
        return ActionResult.makeSuccess(message)

    def abandon(self, state):
        productions = { res: amount for res, amount in self.edge.getInputs().items()
            if res.isProduction or res.isHumanResource }

        teamState = self.teamState(state)
        teamState.resources.returnResources(productions)
        return self.makeAbandon("Tým nedostane zpátky žádné materiály")

    def cancel(self, state):
        teamState = self.teamState(state)
        materials = teamState.resources.returnResources(self.edge.getInputs())
        message = "Vraťte týmu materiály: " + ResourceStorage.asHtml(materials)

        return self.makeCancel(message)
