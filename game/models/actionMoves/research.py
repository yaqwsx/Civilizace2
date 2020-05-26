from django import forms

from game.data.tech import TechEdgeModel, TechModel
from game.data.entity import DieModel
from game.forms.action import MoveForm
from game.models.actionMovesList import ActionMove
from game.models.actionBase import Action
from game.models.state import TechStorageItem, TechStatusEnum


class ResearchForm(MoveForm):
    techSelect = forms.ChoiceField(label="Vyber tech")

    def __init__(self, team, state, *args, **kwargs):
        super().__init__(team=team, state=state, *args, **kwargs)
        techs = state.teamState(team).techs
        researching = [(tech.id, ">> " + tech.label) for tech in techs.getTechsUnderResearch()]
        edges = [(edge.id, edge.label) for edge in techs.getActionableEdges()]
        choices = []
        choices.extend(researching)
        choices.extend(edges)
        self.fields["techSelect"].choices = choices

class ResearchMove(Action):
    class Meta:
        proxy = True
    class CiviMeta:
        move = ActionMove.research
        form = ResearchForm
    def requiresDice(self, state):
        return True

    def dotsRequired(self, state):
        return { DieModel.objects.get(id="die-any"): 1 }

    @property
    def selectId(self):
        return self.arguments["selectId"]

    teamState = None
    status = None
    tech = None
    edge = None

    @staticmethod
    def build(data):
        action = ResearchMove(team=data["team"], move=data["action"], arguments={"selectId": data["techSelect"]})
        return action

    def sane(self):
        return True

    def preprocess(self, state):
        self.teamState =  state.teamState(self.team.id)

        if self.selectId[:5] != "edge-":
            self.tech = TechModel.objects.get(id=self.selectId)
            assert self.tech is not None, "Failed to decode id " + self.selectId
            self.status = self.teamState.techs.getStatus(self.tech)

            if self.status == TechStatusEnum.UNKNOWN:
                raise Exception("Illegal request: Cannot start researching tech " + self.selectId + " directly")
            return

        self.edge = TechEdgeModel.objects.get(id=self.selectId)
        self.tech = self.edge.dst
        assert self.edge is not None, "Failed to decode id " + self.selectId
        self.status = self.teamState.techs.getStatus(self.tech)

        return

    def initiate(self, state):
        self.preprocess(state)

        if self.status == TechStatusEnum.OWNED:
            return False, "Technologie " + self.tech.label + " už je vyzkoumaná"

        if self.status == TechStatusEnum.RESEARCHING:
            self.teamState.techs.setStatus(self.tech, TechStatusEnum.OWNED)
            print("state changed by initiate")
            return True, "Vyzkoumali jste technologii " + self.tech.label + "; Dostanete spoooustu nalepek"

        return True, "Zacinate zkoumat tech " + self.tech.label + "; Chcete se do toho pustit?"

    def commit(self, state):
        print("Commit")
        self.preprocess(state)

        if self.status != TechStatusEnum.UNKNOWN:
            return True, "Vyhledove se tenhle status nebude zobrazovat, protoze uz mate vyzkoumano"

        self.teamState.techs.setStatus(self.tech, TechStatusEnum.RESEARCHING)
        return True, "Zacali jste zkoumat tech " + self.tech.label + ". Hodne stesti"

    def abandon(self, state):
        return True, self.abandonMessage()

    def cancel(self, state):
        return True, self.cancelMessage()