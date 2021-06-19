import math
from django import forms
from django.core.validators import MaxValueValidator, MinValueValidator
from crispy_forms.layout import Layout, Fieldset, HTML

from game.data import ResourceModel
from game.data.vyroba import VyrobaModel, VyrobaEnhancedImage
from game.forms.action import MoveForm
from game.models.actionBase import Action, InvalidActionException, ActionResult
from game.models.actionTypeList import ActionType
from game.models.state import ResourceStorage, MissingDistanceError, TechStatusEnum

def hideableEnhancers():
    return """
    <script>
        var checkboxes = document.querySelectorAll('.checkboxinput');
        function hideShow() {
            for (var i = 0; i != checkboxes.length; i++) {
                div = document.getElementById("inputs-" + checkboxes[i].name);
                if (div) {
                    if (checkboxes[i].checked) {
                        div.classList.remove("hidden");
                    } else {
                        div.classList.add("hidden");
                    }
                }
            }
        }

        for (var i = 0; i != checkboxes.length; i++) {
            checkboxes[i].addEventListener('change', hideShow);
        }

        hideShow();
    </script>
    """

def scalableAmounts(field):
    return """
    <script>
        var amounts = document.querySelectorAll('.vyrobaAmount');
        var input = document.getElementById('""" + field.id_for_label + """');
        function updateAmounts() {
            volume = parseInt(input.value);
            for (var i = 0; i != amounts.length; i++) {
                amount = amounts[i];
                amount.innerHTML = amount.dataset.amount * volume;
            }
        }
        input.addEventListener("change", updateAmounts);
        updateAmounts();
    </script>
    """

def scalableAmount(amount):
    return f'<span class="vyrobaAmount" data-amount="{amount}">{amount}</span>'

def vyrobaEnhanced(state, teamId, vyrobaId):
    """
    Return vyroba with its enhancers if available to the team
    """
    teamState = state.teamState(teamId)
    techs = teamState.techs
    vyroba = state.context.vyrobas.get(id=vyrobaId)
    if vyroba.tech.island is None:
        if vyroba not in techs.availableVyrobas():
            raise InvalidActionException("Tým nevlastní tuto výrobu.")
        enhancers = state.teamState(teamId).enhancers.getOwnedEnhancers(vyrobaId)
    else:
        enhancers = []
    return VyrobaEnhancedImage(vyroba, enhancers)

def inputsLabel(inputs):
    return ", ".join([f"{scalableAmount(amount)}&times; {res.label}" for res, amount in inputs.items()])

def enhancerLabel(enhancer):
    if enhancer.amount > 0:
        amountTxt = f"+{enhancer.amount}"
    else:
        amountTxt = f"{enhancer.amount}"
    output = f"{scalableAmount(amountTxt)} {enhancer.vyroba.output.label}"
    return f'<span class="text-xl my-2">{enhancer.label} &#8594; {output}</span>'


class VyrobaForm(MoveForm):
    volumeSelect = forms.IntegerField(label="Počet výrob", validators=[MinValueValidator(1)], initial=1)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        entity = self.getEntity(VyrobaModel)
        self.vyroba = vyrobaEnhanced(self.state, self.teamId, entity.id)

        techs = self.state.teamState(self.teamId).techs
        resources = self.state.teamState(self.teamId).resources
        if techs.getStatus(self.vyroba.build) != TechStatusEnum.OWNED:
            raise InvalidActionException(
                f'Nemůžu provádět výrobu <i>{self.vyroba.label}</i>, jelikož tým nemá budovu <i>{self.vyroba.build.label}</i>')

        if techs.getStatus(self.vyroba.tech) != TechStatusEnum.OWNED:
            raise InvalidActionException(
                f'Nemůžu provádět výrobu <i>{self.vyroba.label}</i> jelikož ji tým nevlastní. Výrobu odemyká <i>{self.vyroba.tech.label}</i>')

        inputsLayout = []
        self.vyrobaInputs = {}
        inputsLayout.append(HTML(f'<div>'))
        inputsLayout.append(HTML(
            f'<h3 class="text-xl my-2">{self.vyroba.label} &#8594; {inputsLabel(self.vyroba.getOutput())}</h3>'))
        for resource, amount in self.vyroba.getInputs().items():
            if resource.isTracked:
                continue
            typeId = self.vyroba.id + "-" + resource.id
            label = f'<span class="text-black">{resource.label} (potřeba {scalableAmount(amount)}&times;)</span>'
            choices = [(x.id, x.label) for x in resource.concreteResources()]
            self.fields[typeId] = \
                forms.ChoiceField(choices=choices, label=label)
            self.vyrobaInputs[resource.id] = typeId
            inputsLayout.append(typeId)
        for resource, amount in self.vyroba.getInputs().items():
            if not resource.isTracked:
                continue
            typeId = self.vyroba.id + "-" + resource.id
            label = f'{resource.label} (potřeba {scalableAmount(amount)}&times;)'
            choices = [(x.id, x.label) for x in resource.concreteResources()]
            choicesExtended = []
            for id, myLabel in choices:
                available = resources.get(id)
                if available >= amount:
                    choicesExtended.append((id, f'{myLabel} ({available}x)'))
            self.fields[typeId] = \
                forms.ChoiceField(choices=choicesExtended, label=label)
            self.vyrobaInputs[resource.id] = typeId
            if resource.id == "res-obyvatel" or resource.id == "res-obyvatel":
                self.fields[typeId].widget = forms.HiddenInput()
                self.fields[typeId].initial = choices[0][0]

            inputsLayout.append(typeId)
        inputsLayout.append(HTML(f'</div>'))

        costHtml = inputsLabel(self.vyroba.getInputs())
        self.helper.layout = Layout(
            self.commonLayout,
            'volumeSelect',
            *inputsLayout,
            HTML(scalableAmounts(self["volumeSelect"])),
            HTML(hideableEnhancers())
        )
        return

    def clean(self):
        cleaned_data = super().clean()
        cleaned_data["vyrobaInputs"] = {
            res: cleaned_data[field] for res, field in self.vyrobaInputs.items()
        }
        cleaned_data["enhInputs"] = {}
        for field in self.vyrobaInputs.values():
            del cleaned_data[field]
        return cleaned_data

class VyrobaMove(Action):
    class Meta:
        proxy = True
    class CiviMeta:
        move = ActionType.vyroba
        form = VyrobaForm
        allowed = ["super", "org"]

    @staticmethod
    def build(data):
        action = VyrobaMove(
            team=data["team"],
            move=data["action"],
            arguments={
                **Action.stripData(data)
        })
        print(action.arguments)
        return action

    @staticmethod
    def relevantEntities(state, team):
        techs = state.teamState(team.id).techs

        results = []
        results.extend(techs.getVyrobas())

        for island in state.teamIslands(team):
             results.extend(island.techs.getVyrobas())

        return results

    @property
    def volume(self):
        return self.arguments["volumeSelect"]

    @property
    def die(self):
        return self.vyroba.die

    @property
    def dots(self):
        return 0 if self.vyroba.dots == 0 else math.ceil((self.vyroba.dots * (self.volume+1)) / 2)

    @property
    def vyrobaInputs(self):
        return self.arguments["vyrobaInputs"]

    def precomputeVyroba(self, state):
        self.vyroba = vyrobaEnhanced(state, self.team.id, self.arguments["entity"])

    def requiresDice(self, state):
        self.precomputeVyroba(state)
        return self.dots > 0

    def dotsRequired(self, state):
        self.precomputeVyroba(state)
        return {self.die: self.dots}

    def computeCost(self):
        cost = {}
        costErrorMessage = []
        for resource, amount in self.vyroba.getInputs().items():
            try:
                tmp = self.vyrobaInputs[resource.id]
                cRes = self.context.resources.get(id=self.vyrobaInputs[resource.id])
                if not cRes.isSpecializationOf(resource):
                    costErrorMessage.append(
                        f"Materiál {cRes.label} není specializací {resource.label} ({self.vyroba.label})")
                amount = amount * self.volume
                cost[cRes] = cost.get(cRes, 0) + amount
            except ResourceModel.DoesNotExist:
                costErrorMessage.append(f"Zdroj {self.vyrobaInputs[resource.id]} neexistuje ({self.vyroba.label})")
            except KeyError:
                costErrorMessage.append(f"Zdroj {resource.label} nebyl určen ({self.vyroba.label})")

        if costErrorMessage:
            msgBody = "\n".join([f'<li>{x}</li>' for x in costErrorMessage])
            raise InvalidActionException(f'<ul class="list-disc px-4">{msgBody}</ul>')
        return cost

    def gain(self):
        gain = self.vyroba.amount
        return self.volume * gain

    def rememberCost(self, costDict):
        """
        Remember cost in the arguments - originally not needed, but with
        the transport capacity auto increase it is needed. Based on this, we can
        recover the resource in abandon/cancel.
        """
        if "cost" not in self.arguments:
            self.arguments["cost"] = {}
        for res, amount in costDict.items():
            self.arguments["cost"][res.id] = self.arguments["cost"].get(res.id, 0) + amount

    def retrieveCost(self):
        return {
            self.context.resources.get(id=res): amount for res, amount in self.arguments["cost"].items()
        }

    def initiate(self, state):
        self.state = state
        teamState = state.teamState(self.team.id)
        techs = teamState.techs
        self.precomputeVyroba(state)

        if techs.getStatus(self.vyroba.build) != TechStatusEnum.OWNED:
            return ActionResult.makeFail(f'Nemůžu provádět výrobu, jelikož tým nemá budovu <i>{self.vyroba.build.label}</i>')

        if techs.getStatus(self.vyroba.tech) != TechStatusEnum.OWNED:
            return ActionResult.makeFail(f'Nemůžu provádět výrobu, jelikož tým tuto výrobu (<i>{self.vyroba.label}</i>) nevlastní. Výrobu odemyká <i>{self.vyroba.tech.label}</i>')

        cost = self.computeCost()
        try:
            materials = teamState.resources.payResources(cost)
            self.rememberCost(cost)
        except ResourceStorage.NotEnoughResourcesException as e:
            resMsg = "\n".join([f'{res.label}: {amount}' for res, amount in e.list.items()])
            message = f'Nedostate zdrojů; chybí: <ul class="list-disc px-4">{resMsg}</ul>'
            return ActionResult.makeFail(message)

        message = f"Tým musí hodit {self.dots}&times; {self.vyroba.die.label}.<br>"
        if len(materials) > 0:
            matMessage = "\n".join([f'<li>{amount}× {res.htmlRepr()}</li>' for res, amount in materials.items()])
            message += f'Tým také musí zaplatit:<ul class="list-disc px-4">{matMessage}</ul>'
        else:
            message += f"Tým vám nic nebude platit<br>"
        message += f"Při úspěchu tým obdrží {self.gain()}&times; {self.vyroba.output.htmlRepr()}."
        return ActionResult.makeSuccess(message)

    def commit(self, state):
        self.precomputeVyroba(state)
        teamState =  state.teamState(self.team.id)
        resources = {self.vyroba.output: self.gain()}
        materials = teamState.resources.receiveResources(resources)
        message = "Tým získal " + ResourceStorage.asHtml(resources) + "<br>"
        if len(materials) > 0:
            message += "<b>Vydej " + ResourceStorage.asHtml(materials) + "</b>"
        return ActionResult.makeSuccess(message)

    def abandon(self, state):
        self.precomputeVyroba(state)
        productions = { res: amount for res, amount in self.retrieveCost().items()
            if res.isProduction or res.isHumanResource }

        teamState = state.teamState(self.team.id)
        teamState.resources.returnResources(productions)

        message = "Týmu se nepodařilo naházet dostatek puntíků<br>"
        message += "<br>"
        message += "Tým nedostane zpátky žádné materiály"
        return ActionResult.makeSuccess(message)

    def cancel(self, state):
        self.precomputeVyroba(state)
        teamState =  state.teamState(self.team.id)
        materials = teamState.resources.returnResources(self.retrieveCost())

        message = "Akce byla zrušena<br>"
        message += "<br>"
        message += "Vraťte týmu materiály: " + ResourceStorage.asHtml(materials)

        return ActionResult.makeSuccess(message)