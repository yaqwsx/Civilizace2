from django import forms

from game.data.tech import TechEdgeModel, TechModel
from game.data.entity import DieModel
from game.forms.action import MoveForm
from game.models.actionMovesList import ActionMove
from game.models.actionBase import Action, InvalidActionException
from game.models.state import TechStorageItem, TechStatusEnum, ResourceStorage


class ResearchForm(MoveForm):
    techSelect = forms.ChoiceField(label="Vyber výzkum")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        techs = self.state.teamState(self.teamId).techs
        src = TechModel.objects.get(id=self.entityId)
        choices = []
        for edge in src.unlocks_tech.all():
            if techs.getStatus(edge.dst) == TechStatusEnum.UNKNOWN:
                choices.append((edge.id, edge.label))

        if not len(choices):
            raise InvalidActionException("Tady už není co zkoumat (" + src.label + ")")
        self.fields["techSelect"].choices = choices

class ResearchMove(Action):
    class Meta:
        proxy = True
    class CiviMeta:
        move = ActionMove.research
        form = ResearchForm
        allowed = ["super", "org"]

    @staticmethod
    def build(data):
        action = ResearchMove(
            team=data["team"],
            move=data["action"],
            arguments=Action.stripData(data))
        return action

    @staticmethod
    def relevantEntities(state, team):
        techs = state.teamState(team.id).techs
        return techs.getOwnedTechs()

    def sane(self):
        return True

    @property
    def edge(self):
        return TechEdgeModel.objects.get(id=self.arguments["techSelect"])

    def requiresDice(self, state):
        return True

    def dotsRequired(self, state):
        return {self.edge.die: self.edge.dots}

    def initiate(self, state):
        teamState = self.teamState(state)
        techs = teamState.techs
        dst = self.edge.dst

        if techs.getStatus(self.edge.src) != TechStatusEnum.OWNED:
            return False, f"Zdrojová technologie {self.edge.src.label} není vyzkoumána."
        dstStatus = techs.getStatus(dst)
        if dstStatus == TechStatusEnum.OWNED:
            return False, f"Cílová technologie {dst.label} už byla kompletně vyzkoumána."
        if dstStatus == TechStatusEnum.RESEARCHING:
            return False, f"Cilová technologie {dst.label} už je zkoumána."

        try:
            print(self.edge.getInputs())
            materials = teamState.resources.payResources(self.edge.getInputs())
            if materials:
                resMsg = "".join([f'<li>{amount}&times; {res.label}</li>' for res, amount in materials.items()])
                costMessage = f'Tým musí zaplatit: <ul class="list-disc px-4">{resMsg}</ul>'
            else:
                costMessage = "Tým nic neplatí"
        except ResourceStorage.NotEnoughResourcesException as e:
            resMsg = "\n".join([f'{res.label}: {amount}' for res, amount in e.list.items()])
            message = f'Nedostate zdrojů; chybí: <ul class="list-disc px-4">{resMsg}</ul>'
            return False, message
        return True, f"""
            Pro vyzkoumání <i>{self.edge.dst.label}</i> skrze <i>{self.edge.label}</i> je třeba hodit: {self.edge.dots}&times; {self.edge.die.label}<br>
            {costMessage}<br>
        """

    def commit(self, state):
        self.teamState(state).techs.setStatus(self.edge.dst, TechStatusEnum.RESEARCHING)
        return True, f"""
            Zkoumání technologie {self.edge.dst.label} bylo započato.<br>
            Musíte splnit úkol: TUTO FUNKCIONALITU JE JETŠTĚ TŘEBA IMPLEMENTOVAT
        """

    def abandon(self, state):
        productions = { res: amount for res, amount in self.edge.getInputs().items()
            if res.isProduction or res.isHumanResource }

        teamState = self.teamState(state)
        teamState.resources.receiveResources(productions)

        message = self.abandonMessage()
        message += "<br>"
        message += "Tým nedostane zpátky žádné materiály"
        return True, message

    def cancel(self, state):
        teamState = self.teamState(state)
        materials = teamState.resources.receiveResources(self.edge.getInputs())

        message = self.cancelMessage()
        message += "<br>"
        message += "Vraťte týmu materiály: " + ResourceStorage.asHtml(materials)

        return True, message