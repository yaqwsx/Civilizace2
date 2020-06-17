import math
from crispy_forms.layout import Layout, Fieldset, HTML
from django import forms

from game.data import ResourceModel
from game.forms.action import MoveForm
from game.models.actionMovesList import ActionMove
from game.models.actionBase import Action, InvalidActionException


class NextTurnForm(MoveForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        generation = self.state.worldState.generation
        team = self.state.teamState(self.teamId)
        turn = team.turn

        if turn >= generation:
            raise InvalidActionException("Tým už v této generaci krmil")

        missingItems = team.foodSupply.getMissingItems(
            self.state.worldState.getCastes(),
            team.resources.getAmount("res-populace"),
            self.state.worldState.foodValue)

        layout = [self.commonLayout]

        # TODO: Formatovat jako nadpis
        layout.append(HTML("""<b>Kvalita jídla</b>"""))
        foodFields = ["Postupně vybírej jídlo odpovídající úrovně:"]
        for i, kasta in enumerate(missingItems, start=1):
            text = f"Úroveň {kasta[0]}: {kasta[6]}× jídlo"
            self.fields["check-satisfied-" + str(i)] = forms.BooleanField(label=text,initial=kasta[6]==0,required=False)
            foodFields.append("check-satisfied-"+str(i))
        layout.append(Fieldset(*foodFields))

        layout.append(HTML("""<hr class="border-2 border-black my-2">"""))
        self.fields["foodTotal"] = forms.IntegerField(
            label=f"Kolik jídla jste vybrali (doporučeno {missingItems[-1][4]})")
        layout.append(Fieldset('Celkové množství jídla', 'foodTotal'))

        layout.append(HTML("""<hr class="border-2 border-black my-2">"""))
        luxusFields = ["Postupně vybírej luxus odpovídající úrovně:"]
        for i, kasta in enumerate(missingItems, start=1):
            text = f"Úroveň {kasta[0]}: {kasta[8]}× luxus"
            self.fields["check-luxus-" + str(i)] = forms.BooleanField(label=text,initial=kasta[6]==0,required=False)
            luxusFields.append("check-luxus-"+str(i))
        layout.append(Fieldset(*luxusFields))


        self.helper.layout = Layout(
            *layout
        )


class NextTurn(Action):
    class Meta:
        proxy = True
    class CiviMeta:
        move = ActionMove.nextTurn
        form = NextTurnForm
        allowed = ["super", "org"]

    @staticmethod
    def relevantEntities(state, team):
        return []

    def build(data):
        action = NextTurn(team=data["team"], move=data["action"], arguments={})
        return action

    def initiate(self, state):
        unfinished = self.team.unfinishedAction()
        print(unfinished)
        if unfinished:
            org = unfinished.actionstep_set.all()[0].author
            message = f"Nelze začít kolo, nedoházeli jste kostkou u organizátora {org.username}"
            return False, message
        return True, "Začíná kolo!"

    def commit(self, state):
        team = self.teamState(state)

        storage = team.resources

        # obyvatele a prace
        praceLeft = storage.getAmount("res-prace")
        obyvatele = storage.getAmount("res-obyvatel")

        prace = obyvatele + math.floor(praceLeft/2)
        print("prace: " + str(prace))
        storage.setAmount("res-prace", prace)

        team.nextTurn()
        message = """Začalo kolo {turn}""".format(turn=team.turn)
        return True, message

