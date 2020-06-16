import math
from django import forms
from django.core.validators import MaxValueValidator, MinValueValidator
from crispy_forms.layout import Layout, Fieldset, HTML

from game.data import ResourceModel
from game.data.vyroba import VyrobaModel, EnhancementModel
from game.forms.action import MoveForm
from game.models.actionBase import Action, InvalidActionException
from game.models.actionMovesList import ActionMove
from game.models.state import ResourceStorage

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

def obtainVyrobaInfo(state, teamId, vyrobaId):
    """
    Return vyroba with its enhancers if available to the team
    """
    teamState = state.teamState(teamId)
    techs = teamState.techs
    vyroba = VyrobaModel.objects.get(id=vyrobaId)
    if vyroba not in techs.availableVyrobas():
        raise InvalidActionException("Tým nevlastní tuto výrobu.")
    return vyroba, techs.availableEnhancements(vyroba)

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
        self.vyroba, self.enhancers = obtainVyrobaInfo(self.state, self.teamId, self.entityId)

        inputsLayout = []
        self.vyrobaInputs = {}
        inputsLayout.append(HTML(f'<div>'))
        inputsLayout.append(HTML(
            f'<h3 class="text-xl my-2">{self.vyroba.label} &#8594; {inputsLabel(self.vyroba.getOutput())}</h3>'))
        for resource, amount in self.vyroba.getInputs().items():
            typeId = self.vyroba.id + "-" + resource.id
            label = f'{resource.label} (potřeba {scalableAmount(amount)}&times;)'
            choices = [(x.id, x.label) for x in resource.concreteResources()]
            self.fields[typeId] = \
                forms.ChoiceField(choices=choices, label=label)
            self.vyrobaInputs[resource.id] = typeId
            inputsLayout.append(typeId)
        inputsLayout.append(HTML(f'</div>'))

        self.enhancersInputs = {}
        for enhancer in self.enhancers:
            self.fields[enhancer.id] = forms.BooleanField(required=False, label=enhancerLabel(enhancer))
            inputsLayout.append(enhancer.id)
            inputsLayout.append(HTML(f'<div id="inputs-{enhancer.id}">'))
            inputsFields = {}
            for resource, amount in enhancer.getInputs().items():
                typeId = enhancer.id + "-" + resource.id
                label = f'{resource.label} (potřeba {scalableAmount(amount)}&times;)'
                choices = [(x.id, x.label) for x in resource.concreteResources()]
                self.fields[typeId] = \
                    forms.ChoiceField(choices=choices, label=label)
                inputsFields[resource.id] = typeId
                inputsLayout.append(typeId)
            self.enhancersInputs[enhancer.id] = inputsFields
            inputsLayout.append(HTML('</div>'))

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
        for enh, inputs in self.enhancersInputs.items():
            cleaned_data["enhInputs"] = {
                res: cleaned_data[field] for res, field in inputs.items()
            }
        for field in self.vyrobaInputs.values():
            del cleaned_data[field]
        for inputs in self.enhancersInputs.values():
            for field in inputs.values():
                del cleaned_data[field]
        return cleaned_data

class VyrobaMove(Action):
    class Meta:
        proxy = True
    class CiviMeta:
        move = ActionMove.vyroba
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

        return results

    @property
    def volume(self):
        return self.arguments["volumeSelect"]

    @property
    def vyroba(self):
        return VyrobaModel.objects.get(id=self.arguments["entity"])

    @property
    def die(self):
        return self.vyroba.die

    @property
    def dots(self):
        return 0 if self.vyroba.dots == 0 else math.ceil((self.vyroba.dots * self.volume+1) / 2)

    @property
    def vyrobaInputs(self):
        return self.arguments["vyrobaInputs"]

    @property
    def enhInputs(self):
        return self.arguments["enhInputs"]

    def active(self, enhancementId):
        return self.arguments[enhancementId]

    def requiresDice(self, state):
        return True

    def dotsRequired(self, state):
        return {self.die: self.dots}

    def computeCost(self):
        cost = {}
        costErrorMessage = []
        for resource, amount in self.vyroba.getInputs().items():
            try:
                cRes = ResourceModel.objects.get(id=self.vyrobaInputs[resource.id])
            except ResourceModel.DoesNotExist:
                costErrorMessage += f"Zdroj {self.vyrobaInputs[resource.id]} neexistuje ({self.vyroba.label})"
            except KeyError:
                costErrorMessage += f"Zdroj {resource.label} nebyl určen ({self.vyroba.label})"
            if not cRes.isSpecializationOf(resource):
                costErrorMessage.append(f"Materiál {cRes.label} není specializací {resource.label} ({self.vyroba.label})")
            amount = amount * self.volume
            cost[resource] = cost.get(resource, 0) + amount

        for enh in self.vyroba.enhancers.all():
            if not self.active(enh.id):
                continue
            for resource, amount in enh.getInputs().items():
                try:
                    cRes = ResourceModel.objects.get(id=self.vyrobaInputs[resource.id])
                except ResourceModel.DoesNotExist:
                    costErrorMessage += f"Zdroj {self.vyrobaInputs[resource.id]} neexistuje ({enh.label})"
                except KeyError:
                    costErrorMessage += f"Zdroj {resource.label} nebyl určen ({enh.label})"
                if not cRes.isSpecializationOf(resource):
                    costErrorMessage.append(f"Materiál {cRes.label} není specializací {resource.label} ({enh.label})")
                amount = amount * self.volume
                cost[resource] = cost.get(resource, 0) + amount
        if costErrorMessage:
            msgBody = "\n".join([f'<li>{x}</li>' for x in costErrorMessage])
            raise InvalidActionException(f'<ul>{msgBody}</ul>')
        return cost

    def computeDistance(self):
        pass

    def gain(self):
        gain = self.vyroba.amount
        for enh in self.vyroba.enhancers.all():
            if self.active(enh.id):
                gain += enh.amount
        return self.volume * gain

    def initiate(self, state):
        teamState =  state.teamState(self.team.id)

        cost = self.computeCost()
        try:
            materials = teamState.resources.payResources(cost)
        except ResourceStorage.NotEnoughResourcesException as e:
            resMsg = "\n".join([f'{res.label}: {amount}' for res, amount in e.list.items()])
            message = f'Nedostate zdrojů; chybí: <ul>{resMsg}</ul>'
            return False, message
        message = f"Tým musí hodit {self.dots}&times; {self.vyroba.die.label}.<br>"
        if len(materials) > 0:
            matMessage = "\n".join([f'<li>{res.label}: {amount}</li>' for res, amount in materials.items()])
            message += f"Tým také musí zaplatit:<ul>{matMessage}</ul>"
        else:
            message += f"Tým vám nic nebude platit<br>"
        message += f"Tým obdrží {self.gain()}&times; {self.vyroba.output.label}."
        return True, message

    def commit(self, state):
        teamState =  state.teamState(self.team.id)
        resources = {self.vyroba.output: self.gain()}
        materials = teamState.resources.receiveResources(resources)
        message = "Tým získal " + ResourceStorage.asHtml(resources) + "<br>"
        if len(materials) > 0:
            message += "<b>Vydej " + ResourceStorage.asHtml(materials) + "</b>"
        return True, message

    def abandon(self, state):
        productions = filter(
            lambda resource, amount:
                resource.id[:5] == "prod-"
                or resource.id == "res-obyvatel",
            self.computeCost.items()
        )

        message = self.abandonMessage()
        message += "<br>"
        message += "Tým nedostane zpátky žádné materiály"
        return True, message

    def cancel(self, state):
        teamState =  state.teamState(self.team.id)
        materials = teamState.resources.receiveResources(self.computeCost())

        message = self.cancelMessage()
        message += "<br>"
        message += "Vraťte týmu materiály: " + ResourceStorage.asHtml(materials)

        return True, message