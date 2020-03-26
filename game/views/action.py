from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.http import HttpResponse
from game import models
from game.forms import MoveInitialForm, DiceThrowForm
from game import parameters
from django.db.models import Count, Q

class ActionView(View):
    def unfinishedActionBy(self, user):
        """
        Return one of the unfinished actions by the current user, None otherwise
        """
        unfinished = models.Action.objects \
            .filter(actionstep__author=user) \
            .annotate(
                initcount=Count('actionstep',
                    filter=Q(actionstep__phase=models.ActionPhase.initiate))) \
            .annotate(allcount=Count('actionstep')) \
            .filter(initcount=1, allcount=1)[:1]
        if unfinished:
            return unfinished[0].resolve()
        return None

    def unfinishedMessage(self, action):
        return "Akce \"{}\" nebyla dokončena. Dokončete ji prosím. Teprve poté budete moci zadávat nové akce".format(
            action.description())


class ActionIndexView(ActionView):
    @method_decorator(login_required)
    def get(self, request):
        if not request.user.isOrg():
            raise PermissionDenied("Cannot view the page")
        unfinishedAction = self.unfinishedActionBy(request.user)
        if unfinishedAction:
            messages.warning(request, self.unfinishedMessage(unfinishedAction))
            return redirect('actionDiceThrow', actionId=unfinishedAction.id)
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


class ActionMoveView(ActionView):
    @method_decorator(login_required)
    def get(self, request, teamId, moveId):
        if not request.user.isOrg():
            raise PermissionDenied("Cannot view the page")
        unfinishedAction = self.unfinishedActionBy(request.user)
        if unfinishedAction:
            messages.warning(request, self.unfinishedMessage(unfinishedAction))
            return redirect('actionDiceThrow', actionId=unfinishedAction.id)
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
                "action": action,
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

class ActionConfirmView(ActionView):
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
                    "action": action,
                    "moveValid": moveValid,
                    "message": message,
                    "messages": messages.get_messages(request)
                })
            action.save()
            step.save()
            state.save()
            if action.requiresDice():
                messages.success(request, "Akce \"{}\" započata".format(action.description()))
                return redirect('actionDiceThrow', actionId=action.id)
            messages.success(request, "Akce \"{}\" provedena".format(action.description()))
            return redirect('actionIndex')
        return HttpResponse(status=422)

class ActionDiceThrow(ActionView):
    @method_decorator(login_required)
    def get(self, request, actionId):
        if not request.user.isOrg():
            raise PermissionDenied("Cannot view the page")
        action = get_object_or_404(models.Action, pk=actionId).resolve()
        state = models.State.objects.getNewest()
        teamState = state.teamState(action.team.id)
        if self.isFinished(action):
            messages.error("Akce již byla dokončena. Nesnažíte se obnovit načtenou stránku?")
            return redirect('actionIndex')
        form = DiceThrowForm(action.dotsRequired().keys())
        return render(request, "game/actionDiceThrow.html", {
            "request": request,
            "form": form,
            "team": action.team,
            "action": action,
            "messages": messages.get_messages(request),
            "maxThrows": teamState.population.work // parameters.DICE_THROW_PRICE
        })

    @method_decorator(login_required)
    def post(self, request, actionId):
        if not request.user.isOrg():
            raise PermissionDenied("Cannot view the page")
        action = get_object_or_404(models.Action, pk=actionId).resolve()
        if self.isFinished(action):
            messages.error(request, "Akce již byla dokončena. Nesnažíte se obnovit načtenou stránku?")
            return redirect('actionIndex')
        form = DiceThrowForm(action.dotsRequired().keys(), data=request.POST)
        if not form.is_valid(): # Should be always unless someone plays with API directly
            print(form.errors)
            return HttpResponse(status=422)
        state = models.State.objects.getNewest()
        teamState = state.teamState(action.team.id)
        maxThrowTries = teamState.population.work // parameters.DICE_THROW_PRICE
        if form.cleaned_data["throwCount"] > maxThrowTries:
            messages.error(request, """
                Zadali jste více hodů než na kolik má tým nárok. Tým mohl hodit
                maximálně <b>{}x</b>, hodil však <b>{}x</b>. Pokud to není chyba,
                je možné, že tým házel zároveň i na jiném stanovišti a tam
                spotřeboval práci. V tom případě dokončete akci znovu -- jen
                zadejte maximální počet hodů.""".format(maxThrowTries, form.cleaned_data["throwCount"]))
            return redirect('actionDiceThrow', actionId=action.id)
        if "cancel" in request.POST:
            step = models.ActionStep.cancelAction(request.user, action)
            channel = messages.warning
        else:
            requiredDots = action.dotsRequired()[int(form.cleaned_data["dice"])]
            workConsumed = form.cleaned_data["throwCount"] * parameters.DICE_THROW_PRICE
            if form.cleaned_data["dotsCount"] >= requiredDots:
                step = models.ActionStep.commitAction(request.user, action, workConsumed)
                channel = messages.success
            else:
                step = models.ActionStep.abandonAction(request.user, action, workConsumed)
                channel = messages.warning
            moveValid, message = step.applyTo(state)
            if not moveValid:
                messages.error(message)
                return redirect('actionDiceThrow', actionId=action.id)
            action.save()
            step.save()
            state.save()
            if message and len(message) > 0:
                channel(request, message)
            return redirect('actionIndex')

    def isFinished(self, action):
        return action.actionstep_set.all().exclude(phase=models.ActionPhase.initiate).exists()