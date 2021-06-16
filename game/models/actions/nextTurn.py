import math
from crispy_forms.layout import Layout, Fieldset, HTML
from django import forms

from game.data import ResourceModel
from game.forms.action import MoveForm
from game.models.actionTypeList import ActionType
from game.models.actionBase import Action, InvalidActionException, ActionResult


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
            team.resources.get("res-populace"),
            self.state.worldState.foodValue)

        layout = [self.commonLayout]

        # TODO: Formatovat jako nadpis
        layout.append(HTML("""<b>Kvalita jídla</b>"""))
        foodFields = ["Postupně vybírej jídlo odpovídající úrovně:"]
        for i, kasta in enumerate(missingItems, start=1):
            text = f"{kasta[6]}× jídlo <b>{kasta[0]}</b>"
            self.fields["check-satisfied-" + str(i)] = forms.BooleanField(label=text,initial=kasta[6]==0,required=False)
            foodFields.append("check-satisfied-"+str(i))
        layout.append(Fieldset(*foodFields))

        layout.append(HTML("""<hr class="border-2 border-black my-2">"""))
        self.fields["foodTotal"] = forms.IntegerField(
            label=f"Kolik jídla jste vybrali (doporučeno {missingItems[-1][4]})", initial=missingItems[-1][4])
        layout.append(Fieldset('Celkové množství jídla', 'foodTotal'))

        layout.append(HTML("""<hr class="border-2 border-black my-2">"""))
        luxusFields = ["Postupně vybírej luxus odpovídající úrovně:"]
        for i, kasta in enumerate(missingItems, start=1):
            text = f"Úroveň {kasta[0]}: {kasta[8]}× luxus"
            self.fields["check-luxus-" + str(i)] = forms.BooleanField(label=text,initial=kasta[8]==0,required=False)
            luxusFields.append("check-luxus-"+str(i))
        layout.append(Fieldset(*luxusFields))


        self.helper.layout = Layout(
            *layout
        )


class NextTurn(Action):
    class Meta:
        proxy = True
    class CiviMeta:
        move = ActionType.nextTurn
        form = NextTurnForm
        allowed = ["super", "org"]

    @staticmethod
    def relevantEntities(state, team):
        return []

    def build(data):
        action = NextTurn(team=data["team"], move=data["action"], arguments={**data})
        action.arguments["team"] = None
        return action

    def initiate(self, state):
        unfinished = self.team.unfinishedAction()

        if unfinished:
            org = unfinished.actionevent_set.all()[0].author
            result = ActionResult.makeFail(f"Nelze začít kolo, nedoházeli jste kostkou u organizátora {org.username}")
            return result

        return ActionResult.makeSuccess()

    def commit(self, state):
        team = self.teamState(state)

        storage = team.resources

        # Vyhodnoceni mnozeni obyvatel
        missingItems = team.foodSupply.getMissingItems(
            state.worldState.getCastes(),
            team.resources.get("res-populace"),
            state.worldState.foodValue)

        foodProvided = self.arguments["foodTotal"]
        prirustek = 0
        for i, kasta in enumerate(missingItems, start=1):
            satisfied = self.arguments["check-satisfied-"+str(i)]
            luxus = self.arguments["check-luxus-"+str(i)]

            if foodProvided >= kasta[4]:
                prirustek += 1
            else:
                prirustek -= 5
            if satisfied: prirustek += 1
            if luxus: prirustek += 2

        praceLeft = storage.get("res-prace")
        obyvatele = storage.get("res-obyvatel")
        obyvateleUpdated = obyvatele + prirustek

        storage.set("res-obyvatel", obyvateleUpdated)
        prace = obyvateleUpdated + math.floor(praceLeft/2)
        storage.set("res-prace", prace)

        # Produkce materialu
        materials = {}
        for resource, amount in team.resources.getResourcesByType().items():
            matId = "mat-" + resource.id[6:]
            print("matId: " + str(matId))
            material = self.context.resources.get(id="mat-" + resource.id[5:])
            materials[material] = amount
        team.materials.receiveMaterials(materials, state.worldState.storageLimit)

        team.nextTurn()
        message = "<br>".join([
            f"Začalo kolo {team.turn}",
            f"Máte {prirustek} nových obyvatel",
            f"V tomto kole máte {prace} práce"
        ])
        return ActionResult.makeSuccess(message)

