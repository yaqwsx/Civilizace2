from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.http import HttpResponse
from game import models
from game.forms import MoveInitialForm

class ActionIndexView(View):
    @method_decorator(login_required)
    def get(self, request):
        if not request.user.isOrg():
            raise PermissionDenied("Cannot view the page")
        form = MoveInitialForm()
        return render(request, "game/actionIndex.html", {
            "request": request,
            "form": form,
            "messages": messages.get_messages(request)
        })

    @method_decorator(login_required)
    def post(self, request):
        if not request.user.isOrg():
            raise PermissionDenied("Cannot view the page")
        form = MoveInitialForm(request.POST)
        if form.is_valid():
            return redirect('actionMove',
                moveId=form.cleaned_data['action'].value,
                teamId=form.cleaned_data['team'].id)
        return render(request, "game/actionIndex.html", {
            "request": request,
            "form": form,
            "messages": messages.get_messages(request)
        })


class ActionMoveView(View):
    @method_decorator(login_required)
    def get(self, request, teamId, moveId):
        if not request.user.isOrg():
            raise PermissionDenied("Cannot view the page")
        form = models.Action.formFor(moveId)(teamId, moveId)
        return render(request, "game/actionMove.html", {
            "request": request,
            "form": form,
            "team": get_object_or_404(models.Team, pk=teamId),
            "action": models.ActionMove(moveId),
            "messages": messages.get_messages(request)
        })

    @method_decorator(login_required)
    def post(self, request, teamId, moveId):
        if not request.user.isOrg():
            raise PermissionDenied("Cannot view the page")
        form = models.Action.formFor(moveId)(data=request.POST.copy()) # copy, so we can change the cancelled field
        if form.is_valid() and not form.cleaned_data["canceled"]:
            action = models.Action.build(form.cleaned_data)
            step = models.ActionStep.initiateAction(request.user, action)
            state = models.State.objects.getNewest()
            moveValid, message = step.applyTo(state)

            form.data["canceled"] = True
            return render(request, "game/actionConfirm.html", {
                "request": request,
                "form": form,
                "team": get_object_or_404(models.Team, pk=teamId),
                "action": models.ActionMove(moveId),
                "moveValid": moveValid,
                "message": message,
                "messages": messages.get_messages(request)
            })
        form.data["canceled"] = False
        return render(request, "game/actionMove.html", {
            "request": request,
            "form": form,
            "team": get_object_or_404(models.Team, pk=teamId),
            "action": models.ActionMove(moveId),
            "messages": messages.get_messages(request)
        })

class ActionConfirmView(View):
    @method_decorator(login_required)
    def post(self, request, teamId, moveId):
        if not request.user.isOrg():
            raise PermissionDenied("Cannot view the page")
        form = models.Action.formFor(moveId)(data=request.POST)
        if form.is_valid(): # Should be always unless someone plays with API directly
            action = models.Action.build(form.cleaned_data)
            step = models.ActionStep.initiateAction(request.user, action)
            state = models.State.objects.getNewest()
            moveValid, message = step.applyTo(state)
            if not moveValid:
                form.data["canceled"] = True
                return render(request, "game/actionConfirm.html", {
                    "request": request,
                    "form": form,
                    "team": get_object_or_404(models.Team, pk=teamId),
                    "action": models.ActionMove(moveId),
                    "moveValid": moveValid,
                    "message": message,
                    "messages": messages.get_messages(request)
                })
            state.save()
            messages.success(request, "Akce provedena")
            return redirect('actionIndex')
        return HttpResponse(status=422)