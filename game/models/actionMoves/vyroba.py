import math
from django import forms
from django.core.validators import MaxValueValidator, MinValueValidator
from crispy_forms.layout import Layout, Fieldset, HTML

from game.data import ResourceModel
from game.data.vyroba import VyrobaModel
from game.forms.action import MoveForm
from game.models.actionBase import Action, InvalidActionException
from game.models.actionMovesList import ActionMove
from game.models.state import ResourceStorage


class VyrobaForm(MoveForm):
    volumeSelect = forms.IntegerField(label="Počet výrob", validators=[MinValueValidator(1)])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        vyroba = VyrobaModel.objects.get(id=self.entityId)

        costHtml = ResourceStorage.asHtml(vyroba.getInputs())

        layout = [
            HTML(f"<b>Cena výroby</b>: {costHtml}<br>"),
            HTML(f"<b>Výstup</b>: {ResourceStorage.asHtml(vyroba.getOutput())}<br>"),
            'volumeSelect',
            HTML('<hr class="border-2 border-black my-2">'),
        ]
        productions = {}
        metaProductions = {}
        build = vyroba.build
        teamState = self.state.teamState(self.teamId)

        for resource, amount in vyroba.getInputs().items():
            if not resource.isProduction:
                continue

            if not resource.isMeta:
                # layout.append(HTML(f"Production {resource.id}<br>"))
                productions[resource] = amount
            else:
                # layout.append(HTML(f"Generic production {resource.id}<br>"))
                metaProductions[resource] = amount

        subLayout = ['Vzdálenost vstupů']
        for resource, amount in productions.items():
            distance = teamState.distances.getProductionDistance(resource, build)
            field = forms.IntegerField(label=f"{resource.label}", initial=distance)
            id = f"dist-{resource.id}"
            self.fields[id] = field
            subLayout.append(id)
        layout.append(Fieldset(*subLayout))

        for metaResource, metaAmount in metaProductions.items():
            layout.append(HTML('<hr class="border-2 border-black my-2">'))
            subLayout = [f"{metaResource.label} ({metaAmount}x)"]
            idPrefix = f"meta-{metaResource.id}-"
            fieldData = []

            for resource, resAmount in self.state.teamState(self.teamId).resources.getResourcesByType(metaResource).items():
                distance = teamState.distances.getProductionDistance(resource, build)
                data = ((resource, f"{resource.label} ({resAmount}x)"), resAmount, distance)
                fieldData.append(data)

            if not len(fieldData):
                raise ResourceStorage.NotEnoughResourcesException(f"Nemáte skladem žádné produkce typu {metaResource}")

            print("metaAmount: " + str(metaAmount))
            print("fieldData: " + str(fieldData))
            choices = list(zip(*fieldData))[0]
            sField = forms.ChoiceField(label="Select resource", choices=choices)
            cField = forms.IntegerField(label="Amount", initial=metaAmount)
            dField = forms.IntegerField(label="Vzdalenost", initial=fieldData[0][2])
            self.fields[f"{idPrefix}s-0"] = sField
            self.fields[f"{idPrefix}c-0"] = cField
            self.fields[f"{idPrefix}d-0"] = dField
            subLayout.append(f"{idPrefix}s-0")
            subLayout.append(f"{idPrefix}c-0")
            subLayout.append(f"{idPrefix}d-0")
            layout.append(Fieldset(*subLayout))

        self.helper.layout = Layout(
            self.commonLayout,  # Don't forget to add fields of the base form
            *layout
        )

        print("[*layout]: " + str([*layout]))


class VyrobaMove(Action):
    class Meta:
        proxy = True
    class CiviMeta:
        move = ActionMove.vyroba
        form = VyrobaForm

    @staticmethod
    def build(data):
        action = VyrobaMove(
            team=data["team"],
            move=data["action"],
            arguments={
                **data
        })
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

    vyroba = None
    def preprocess(self, state):
        print("self.arguments: " + str(self.arguments))
        self.vyroba = VyrobaModel.objects.get(id=self.arguments["entity"])
        self.die = self.vyroba.die
        self.dots = 0 if self.vyroba.dots==0 else math.ceil((self.vyroba.dots*self.volume+1)/2)
        self.cost = {}

        productions = {}

        for resource, amount in self.vyroba.getInputs().items():
            if not resource.isProduction:
                self.cost[resource] = amount*self.volume
                continue

            if not resource.isMeta:
                distance = self.arguments[f"dist-{resource.id}"]
                productions[resource] = (amount * self.volume, distance)

        for metaResource, metaAmount in self.vyroba.getInputs().items():
            if not metaResource.isProduction:
                continue
            if metaResource.isMeta and metaResource.isProduction:
                i = 0
                sum = 0
                print("Looking up meta resource: " + str(metaResource))
                while f"meta-{metaResource.id}-s-{i}" in self.arguments:
                    resource = ResourceModel.objects.get(id=self.arguments[f"meta-{metaResource.id}-s-{i}"])
                    amount = self.arguments[f"meta-{metaResource.id}-c-{i}"]
                    distance = self.arguments[f"meta-{metaResource.id}-d-{i}"]
                    sum += amount

                    if resource in productions:
                        entry = productions[resource]
                        productions[resource] = (
                            entry[0] + amount,
                            min(entry[1], distance)
                        )
                    else:
                        productions[resource] = (amount, distance)
                    i += 1
                print(f"{metaResource}: Zaplaceno {sum}, ocekavano")
                if sum != metaAmount*self.volume:
                    raise InvalidActionException(
                        f"Neodpovídá cena {metaResource.label}: Máte zaplatit {metaAmount*self.volume}, zadali jste {sum}")

        print("productions: " + str(productions))
        costs = {key: value[0] for key, value in productions.items()}
        self.cost.update(costs)
        self.distances = {key: value[1] for key, value in productions.items()}
        
        self.arguments["team"] = None

    def requiresDice(self, state):
        print("RequiresDice")
        return True

    def dotsRequired(self, state):
        print("dotsRequired")
        self.preprocess(state)
        return {self.die:self.dots}

    def initiate(self, state):
        print("initiate")
        self.preprocess(state)

        # materials = storage.payResources(self.cost)

        print("self.cost: " + str(self.cost))
        message = "Musíte zaplatit " + ResourceStorage.asHtml(self.cost)
        print(message)
        return True, message


    def commit(self, state):
        print("commit")
        teamState =  state.teamState(self.team.id)
        self.preprocess(state)
        resources = {self.vyroba.output: self.vyroba.amount}
        materials = teamState.resources.receiveResources(resources)
        message = "Tým získal " + ResourceStorage.asHtml(resources) + "<br>" \
                  "<b>Vydej " + ResourceStorage.asHtml(materials) + "</b>"
        print("Vyroba commit message: " + message)
        return True, message

    def abandon(self, state):
        self.preprocess(state)

        productions = filter(
            lambda resource, amount:
                resource.id[:5] == "prod-"
                or resource.id == "res-obyvatel",
            self.cost.items()
        )

        message = self.abandonMessage()
        message += "<br>"
        message += "Tým nedostane zpátky žádné materiály"
        return True, self.abandonMessage()

    def cancel(self, state):
        teamState =  state.teamState(self.team.id)
        self.preprocess(state)
        materials = teamState.resources.receiveResources(self.cost)

        message = self.cancelMessage()
        message += "<br>"
        message += "Vraťte týmu materiály: " + ResourceStorage.asHtml(materials)

        return True, message