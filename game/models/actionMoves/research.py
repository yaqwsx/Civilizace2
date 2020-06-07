from django import forms

from game.data.tech import TechEdgeModel, TechModel
from game.data.entity import DieModel
from game.forms.action import MoveForm
from game.models.actionMovesList import ActionMove
from game.models.actionBase import Action, InvalidActionException
from game.models.state import TechStorageItem, TechStatusEnum


class ResearchForm(MoveForm):
    techSelect = forms.ChoiceField(label="Vyber výzkum")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Team ID is available under self.teamId
        # State is available under self.state
        # Entity ID is available under self.entityId

        techs = self.state.teamState(self.teamId).techs
        src = TechModel.objects.get(id=self.entityId)

        choices = []
        for edge in src.unlocks_tech.all():
            dst = edge.dst
            if techs.getStatus(dst) == TechStatusEnum.OWNED:
                continue
            if techs.getStatus(dst) == TechStatusEnum.RESEARCHING:
                choices.append((edge.id, ">> " + edge.label))
            if techs.getStatus(dst) == TechStatusEnum.UNKNOWN:
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

    @staticmethod
    def relevantEntities(state, team):
        techs = state.teamState(team.id).techs

        results = []
        results.extend(techs.getOwnedTechs())

        return results


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

    def requiresDice(self, state):
        self.preprocess(state)
        return self.status == TechStatusEnum.UNKNOWN

    def dotsRequired(self, state):
        self.preprocess(state)
        return {self.edge.die:self.edge.dots}

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
        # TODO: Implement
        return True, self.abandonMessage()

    def cancel(self, state):
        # TODO: Implement
        return True, self.cancelMessage()