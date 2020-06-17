import math
from django import forms
from django.core.validators import MaxValueValidator, MinValueValidator
from crispy_forms.layout import Layout, Fieldset, HTML

from game.data import ResourceModel
from game.data.vyroba import VyrobaModel, EnhancementModel
from game.forms.action import MoveForm
from game.models.actionBase import Action, InvalidActionException
from game.models.actionMovesList import ActionMove
from game.models.state import ResourceStorage, MissingDistanceError

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
                if resource.isTracked:
                    continue
                typeId = enhancer.id + "-" + resource.id
                label = f'<span class="text-black">{resource.label} (potřeba {scalableAmount(amount)}&times;)</span>'
                choices = [(x.id, x.label) for x in resource.concreteResources()]
                self.fields[typeId] = \
                    forms.ChoiceField(choices=choices, label=label)
                inputsFields[resource.id] = typeId
                inputsLayout.append(typeId)
            for resource, amount in enhancer.getInputs().items():
                if not resource.isTracked:
                    continue
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
            cleaned_data["enhInputs"][enh] = {
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
        return enhancementId in self.arguments and self.arguments[enhancementId]

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
                costErrorMessage.append(f"Zdroj {self.vyrobaInputs[resource.id]} neexistuje ({self.vyroba.label})")
            except KeyError:
                costErrorMessage.append(f"Zdroj {resource.label} nebyl určen ({self.vyroba.label})")
            if not cRes.isSpecializationOf(resource):
                costErrorMessage.append(f"Materiál {cRes.label} není specializací {resource.label} ({self.vyroba.label})")
            amount = amount * self.volume
            cost[cRes] = cost.get(cRes, 0) + amount

        for enh in self.vyroba.enhancers.all():
            if not self.active(enh.id):
                continue
            for resource, amount in enh.getInputs().items():
                try:
                    cRes = ResourceModel.objects.get(id=self.enhInputs[enh.id][resource.id])
                except ResourceModel.DoesNotExist:
                    costErrorMessage.append(f"Zdroj {self.enhInputs[enh.id][resource.id]} neexistuje ({enh.label})")
                except KeyError:
                    costErrorMessage.append(f"Zdroj {resource.label} nebyl určen ({enh.label})")
                if not cRes.isSpecializationOf(resource):
                    costErrorMessage.append(f"Materiál {cRes.label} není specializací {resource.label} ({enh.label})")
                amount = amount * self.volume
                cost[cRes] = cost.get(cRes, 0) + amount
        if costErrorMessage:
            msgBody = "\n".join([f'<li>{x}</li>' for x in costErrorMessage])
            raise InvalidActionException(f'<ul class="list-disc px-4">{msgBody}</ul>')
        return cost

    def cheapestBuilding(self, target, builds):
        distLogger = self.state.teamState(self.team.id).distances
        l = [(b, distLogger.getBuildingDistance(b, target)) for b in builds]
        return min(l, key=lambda x: x[1])

    def computeDistanceCost(self):
        cost = 0
        target = self.vyroba.build
        missingDistances = []
        def computeCost(resource, amount):
            nonlocal cost
            if not resource.isProduction:
                return
            try:
                building, price = self.cheapestBuilding(target, resource.getProductionBuildings())
                cost += self.volume * amount * price
            except MissingDistanceError as e:
                missingDistances.append((e.source, e.target))

        for resource, amount in self.vyroba.getInputs().items():
            computeCost(resource, amount)
        for enh in self.vyroba.enhancers.all():
            if not self.active(enh.id):
                continue
            for resource, amount in enh.getInputs().items():
                computeCost(resource, amount)
        if missingDistances:
            msgBody = "\n".join([f'<li>{source.label}&mdash;{target.label}</li>' for source, target in missingDistances])
            raise InvalidActionException(f'Neexistují následující vzdálenosti: <ul class="list-disc px-4">{msgBody}</ul>')
        return cost

    def gain(self):
        gain = self.vyroba.amount
        for enh in self.vyroba.enhancers.all():
            if self.active(enh.id):
                gain += enh.amount
        return self.volume * gain

    def increaseTransportCapacityBy(self, amount):
        """
        Increase transport capacity and report success and used/missing resources
        """
        tVyroba = VyrobaModel.objects.get(id="vyr-obchod")
        volume = math.ceil(amount / tVyroba.amount)
        # tVyroba does not use any materials, assume that
        cost = {}
        for resource, amount in tVyroba.getInputs().items():
            cost[resource] = amount * volume
        try:
            teamState = self.state.teamState(self.team.id)
            materials = teamState.resources.payResources(cost)
            self.rememberCost(cost)
            t = ResourceModel.objects.get(id="res-nosic")
            teamState.resources.receiveResources({t: tVyroba.amount * volume})
            self.rememberCost({t: -tVyroba.amount * volume})
        except ResourceStorage.NotEnoughResourcesException as e:
            return False, e.list
        return True, cost

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
            ResourceModel.objects.get(id=res): amount for res, amount in self.arguments["cost"]
        }

    def initiate(self, state):
        self.state = state
        teamState = state.teamState(self.team.id)

        cost = self.computeCost()
        try:
            materials = teamState.resources.payResources(cost)
            self.rememberCost(cost)
        except ResourceStorage.NotEnoughResourcesException as e:
            resMsg = "\n".join([f'{res.label}: {amount}' for res, amount in e.list.items()])
            message = f'Nedostate zdrojů; chybí: <ul class="list-disc px-4">{resMsg}</ul>'
            return False, message
        distanceCost = self.computeDistanceCost()
        distanceMessage = f"Přeprava materiálu stojí {distanceCost} přepravní kapacity."
        try:
            t = ResourceModel.objects.get(id="res-nosic")
            teamState.resources.payResources({t: distanceCost})
            self.rememberCost({t: distanceCost})
        except ResourceStorage.NotEnoughResourcesException as e:
            success, incRes = self.increaseTransportCapacityBy(e.list[t])
            if success:
                resMsg = ", ".join([f'{amount}&times; {res.label}' for res, amount in incRes.items()])
                distanceMessage += f"<br>Přepravní kapacita byla automatický zvýšena, bylo použito: {resMsg}"
                teamState.resources.payResources({t: distanceCost})
                self.rememberCost({t: distanceCost})
            else:
                resMsg = ", ".join([f'{amount}&times; {res}' for amount, res in incRes])
                return False, f"Nepodařilo se zvýšit přepravní kapacitu; chybí {resMsg}"

        message = f"Tým musí hodit {self.dots}&times; {self.vyroba.die.label}.<br>"
        message += distanceMessage + "<br>"
        if len(materials) > 0:
            matMessage = "\n".join([f'<li>{res.label}: {amount}</li>' for res, amount in materials.items()])
            message += f'Tým také musí zaplatit:<ul class="list-disc px-4">{matMessage}</ul>'
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
            lambda resource, amount: resource.isProduction or resource.isHumanResource,
            self.retrieveCost.items()
        )
        teamState = state.teamState(self.team.id)
        teamState.resources.receiveResources(productions)

        message = self.abandonMessage()
        message += "<br>"
        message += "Tým nedostane zpátky žádné materiály"
        return True, message

    def cancel(self, state):
        teamState =  state.teamState(self.team.id)
        materials = teamState.resources.receiveResources(self.retrieveCost())

        message = self.cancelMessage()
        message += "<br>"
        message += "Vraťte týmu materiály: " + ResourceStorage.asHtml(materials)

        return True, message