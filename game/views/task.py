from game.data.entity import AssignedTask, TaskMapping
from django.views import View
from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django import forms
from django_enumfield.forms.fields import EnumChoiceField
from django.forms import formset_factory


from game.data.tech import TaskModel, TechModel

class TaskForm(forms.Form):
    name = forms.CharField(label="Název úkolu")
    capacity = forms.IntegerField(label="Kapacita", min_value=0, initial=10)
    teamDescription = forms.CharField(label="Popis pro tým",
        widget=forms.Textarea(attrs={
            "oninput": "auto_grow(this)",
            "rows": 8
        }))
    orgDescription = forms.CharField(label="Popis pro orga",
        widget=forms.Textarea(attrs={
            "oninput": "auto_grow(this)",
            "rows": 8
        }))

class TaskChoiceField(forms.ModelChoiceField):
    def __init__(self, *args, **kwargs):
        super().__init__(
            queryset=TaskModel.objects.all(), *args, **kwargs)

    def label_from_instance(self, obj):
        return "{} ({})".format(obj.name, obj.id)

class TaskAssignmentForm(forms.Form):
    task = TaskChoiceField(required=False, label="Úkol")

TaskAssignmentFormset = formset_factory(TaskAssignmentForm, extra=1)

class TechTaskMappingForm(forms.Form):
    tech = forms.CharField(widget=forms.HiddenInput())

class TaskIndexView(View):
    @method_decorator(login_required)
    def get(self, request):
        if not request.user.isOrg():
            raise PermissionDenied("Cannot view the page")
        return render(request, "game/taskIndex.html", {
            "request": request,
            "messages": messages.get_messages(request),
            "tasks": TaskModel.objects.all()
        })

class NewTaskView(View):
    @method_decorator(login_required)
    def get(self, request):
        if not request.user.isOrg():
            raise PermissionDenied("Cannot view the page")
        taskForm = TaskForm()
        return render(request, "game/taskEdit.html", {
            "request": request,
            "messages": messages.get_messages(request),
            "form": taskForm
        })

    @method_decorator(login_required)
    def post(self, request):
        if not request.user.isOrg():
            raise PermissionDenied("Cannot view the page")
        taskForm = TaskForm(request.POST)
        if taskForm.is_valid():
            task = TaskModel.objects.create(
                name=taskForm.cleaned_data["name"],
                teamDescription=taskForm.cleaned_data["teamDescription"],
                orgDescription=taskForm.cleaned_data["orgDescription"],
                capacity=taskForm.cleaned_data["capacity"]
            )
            messages.success(request, f"Úkol '{task.name}' vytvořen")
            return redirect("taskTaskIndex")
        return render(request, "game/taskEdit.html", {
            "request": request,
            "messages": messages.get_messages(request),
            "form": taskForm
        })

class EditTaskView(View):
    @method_decorator(login_required)
    def get(self, request, taskId):
        if not request.user.isOrg():
            raise PermissionDenied("Cannot view the page")
        task = get_object_or_404(TaskModel, pk=taskId)
        taskForm = TaskForm(initial={
            "name": task.name,
            "capacity": task.capacity,
            "teamDescription": task.teamDescription,
            "orgDescription": task.orgDescription
        })
        return render(request, "game/taskEdit.html", {
            "request": request,
            "messages": messages.get_messages(request),
            "form": taskForm,
            "edit": True
        })

    @method_decorator(login_required)
    def post(self, request, taskId):
        if not request.user.isOrg():
            raise PermissionDenied("Cannot view the page")
        task = get_object_or_404(TaskModel, pk=taskId)
        taskForm = TaskForm(data=request.POST)
        if taskForm.is_valid():
            task.name = taskForm.cleaned_data["name"]
            task.capacity = taskForm.cleaned_data["capacity"]
            task.orgDescription = taskForm.cleaned_data["orgDescription"]
            task.teamDescription = taskForm.cleaned_data["teamDescription"]
            task.save()
            messages.success(request, f"Úkol '{task.name}' upraven")
            return redirect("taskTaskIndex")
        return render(request, "game/taskEdit.html", {
            "request": request,
            "messages": messages.get_messages(request),
            "form": taskForm,
            "edit": True
        })

class TaskMappingIndexView(View):
    @method_decorator(login_required)
    def get(self, request):
        if not request.user.isOrg():
            raise PermissionDenied("Cannot view the page")
        return render(request, "game/taskMappingIndex.html", {
            "request": request,
            "messages": messages.get_messages(request),
            "techs": self.buildTechsData()
        })

    @method_decorator(login_required)
    def post(self, request):
        if not request.user.isOrg():
            raise PermissionDenied("Cannot view the page")
        techTaskMappingForm = TechTaskMappingForm(request.POST)
        assignment = TaskAssignmentFormset(data=request.POST)
        if techTaskMappingForm.is_valid() and assignment.is_valid():
            tech = TechModel.manager.latest().get(pk=techTaskMappingForm.cleaned_data["tech"])
            tasks = set([x["task"].id for x in assignment.cleaned_data if "task" in x and x["task"] is not None])
            self.updateMapping(tech, tasks)
            messages.success(request, f"Úkoly pro technologii '{tech.label}' upraveny")
            return redirect(reverse("taskMappingIndex") + "#" + tech.id)
        return render(request, "game/taskMappingIndex.html", {
            "request": request,
            "messages": messages.get_messages(request),
            "techs": self.buildTechsData()
        })

    def updateMapping(self, tech, activeTasksIds):
        mappings = TaskMapping.objects.filter(tech=tech).all()
        existingSet = set()
        for m in mappings:
            m.active = m.task.id in activeTasksIds
            existingSet.add(m.task.id)
            m.save()
        for t in activeTasksIds:
            if t in existingSet:
                continue
            TaskMapping.objects.create(
                tech=tech,
                task=TaskModel.objects.get(pk=t))

    def buildTechsData(self):
        return [
            {
                "tech": t,
                "completedBy": AssignedTask.objects.filter(tech=t.id, completedAt__isnull=False).all(),
                "assigned": AssignedTask.objects.filter(tech=t.id, completedAt__isnull=True).all(),
                "mappingForm": TechTaskMappingForm(initial={"tech": t.id}),
                "assignementForm": TaskAssignmentFormset(initial=[
                    {"task": m.task.id} for m in TaskMapping.objects.filter(tech=t, active=True).all()])
            } for t in TechModel.manager.latest().all()
        ]