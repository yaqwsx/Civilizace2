from django.template.loader import render_to_string
from game.data.task import TaskMapping, TaskModel
from django import forms

from game.data.tech import TechEdgeModel, TechModel
from game.data.entity import DieModel
from game.forms.action import MoveForm
from game.models.users import Team
from game.models.actionTypeList import ActionType
from game.models.actionBase import Action, InvalidActionException, ActionResult
from game.models.state import TechStatusEnum, ResourceStorage
from crispy_forms.layout import Layout, Fieldset, HTML


class ResearchForm(MoveForm):
    techSelect = forms.ChoiceField(label="Vyber výzkum")
    taskSelect = forms.ChoiceField(label="Vyber úkol", required=False)
    allTaskSelect = forms.ChoiceField(label="Pokud nevyhovuje, vyber libovolný úkol",
        required=False)

    def taskLabel(self, task):
        label = f"{task.name} ({task.activeCount}/{task.capacity})"
        return label

    def jsMagic(self, mapping):
        return render_to_string("game/fragments/researchFormJs.html", {
            "mapping": mapping
        })

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        techs = self.state.teamState(self.teamId).techs
        src = self.getEntity(TechModel)
        choices = []
        techMapping = {}
        for edge in src.unlocks_tech.all():
            if techs.getStatus(edge.dst) == TechStatusEnum.UNKNOWN:
                choices.append((edge.id, edge.label))
                techMapping[edge.id] = [t.task for t in
                    TaskMapping.objects.filter(
                        techId=edge.dst.id,
                        active=True)
                    if not t.task.assignedTo(Team.objects.get(pk=self.teamId))]

        if not len(choices):
            raise InvalidActionException("Tady už není co zkoumat (" + src.label + ")")
        self.fields["techSelect"].choices = choices

        candidateTasks = set()
        for v in techMapping.values():
            candidateTasks.update(v)
        candidateTasks = [(t.id, self.taskLabel(t)) for t in candidateTasks]
        candidateTasks.sort(key=lambda x: x[1])
        candidateTasks.append(("", "Bez plnění úkolu"))
        self.fields["taskSelect"].choices = candidateTasks

        allTasks = [(t.id, self.taskLabel(t)) for t in TaskModel.objects.all()
            if not t.assignedTo(Team.objects.get(pk=self.teamId))]
        allTasks.sort(key=lambda x: x[1])
        allTasks = [(None, "Nic nevybráno")] + allTasks
        self.fields["allTaskSelect"].choices = allTasks

        self.helper.layout = Layout(
            self.commonLayout,
            "techSelect",
            "taskSelect",
            "allTaskSelect",
            HTML(self.jsMagic(techMapping)),
        )


class ResearchMove(Action):
    class Meta:
        proxy = True
    class CiviMeta:
        move = ActionType.research
        form = ResearchForm
        allowed = ["super", "org"]

    @staticmethod
    def build(data):
        arguments = Action.stripData(data)
        if len(arguments["allTaskSelect"]) > 0:
            taskId = arguments["allTaskSelect"]
        else:
            taskId = arguments["taskSelect"]
        if len(taskId):
            taskId = int(taskId)
        else:
            taskId = None
        del arguments["taskSelect"]
        del arguments["allTaskSelect"]
        arguments["task"] = taskId
        action = ResearchMove(
            team=data["team"],
            move=data["action"],
            arguments=arguments)
        return action

    @staticmethod
    def relevantEntities(state, team):
        techs = state.teamState(team.id).techs
        return techs.getOwnedTechs()

    @property
    def edge(self):
        tech = self.context.edges.get(id=self.arguments["techSelect"])
        return tech

    def requiresDice(self, state):
        return True

    def dotsRequired(self, state):
        return {self.edge.die: self.edge.dots}

    def initiate(self, state):
        teamState = self.teamState(state)
        techs = teamState.techs
        dst = self.edge.dst

        if not self.arguments["task"]:
            task = None
        else:
            try:
                task = TaskModel.objects.get(pk=self.arguments["task"])
            except TaskModel.DoesNotExist as e:
                return ActionResult.makeFail(f"Vybrán neexistující úkol")


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
                resMsg = "".join([f'<li>{amount}&times; {res.label}</li>' for res, amount in materials.items()])
                costMessage = f'Tým musí zaplatit: <ul class="list-disc px-4">{resMsg}</ul>'
            else:
                costMessage = "Tým nic neplatí"
        except ResourceStorage.NotEnoughResourcesException as e:
            resMsg = "\n".join([f'{res.label}: {amount}' for res, amount in e.list.items()])
            message = f'Nedostate zdrojů; chybí: <ul class="list-disc px-4">{resMsg}</ul>'
            return ActionResult.makeFail(message)
        return ActionResult.makeSuccess(
            f"""
                Pro vyzkoumání <i>{self.edge.dst.label}</i> je třeba hodit: {self.edge.dots}&times; {self.edge.die.label}<br>
                {costMessage}<br>
            """)

    def commit(self, state):
        self.teamState(state).techs.setStatus(self.edge.dst, TechStatusEnum.RESEARCHING)
        message = f"Zkoumání technologie {self.edge.dst.label} bylo započato."
        if not self.arguments["task"]:
            task = None
            message += "<br/>Tým nemusí plnit žádný úkol. Přejděte rovnou na akci 'Dokončení výzkumu'"
        else:
            task = TaskModel.objects.get(pk=self.arguments["task"])

        result = ActionResult.makeSuccess(message)
        if task:
            result.startTask(task, self.edge.dst)
        return result

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