from django.views import View
from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.utils.http import urlencode
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.http import HttpResponse
from django.db.models import Count, Q
from django.utils import timezone

from game import models
from game.models.actions import *
from game.models.actionTypeList import ActionType
from game.models.actionBase import Action, ActionContext, ActionEvent, ActionPhase, InvalidActionException
from game.models.users import User, Team
from game.models.state import State
from game.data.task import AssignedTask

from game.forms.action import MoveInitialForm, DiceThrowForm

from game import parameters

def awardAchievements(request, state, team):
    for ach in state.teamState(team).achievements.awardNewAchievements(state, team):
        messages.info(request, f"Tým {team.name} získal achievement <b>{ach.label}</b>!<br>{ach.orgMessage}")

def awardStickers(request, state, team, stickers, commit=False):
    if len(stickers) == 0:
        return ""
    msg = "Tým obdržel samolepky: "
    for s in stickers:
        s.id = None
        s.state = state
        s.team = team
        if commit:
            s.save()
    msg = render_to_string("game/fragments/awardedStickers.html", {
        "stickers": stickers,
        "committed": commit
    })
    return msg

def handleNewTasks(request, state, team, newTasks, finishedTasks, commit=False):
    if len(newTasks) + len(finishedTasks) == 0:
        return ""
    messages = []

    for task, tech in newTasks:
        if commit:
            AssignedTask.objects.create(
                task=task, team=team, techId=tech.id,
                assignedAt = timezone.now(),
                completedAt = None)
        messages.append(render_to_string("game/fragments/awardedTask.html", {
            "task": task,
            "tech": tech,
            "committed": commit
        }))

    if commit:
        for t in finishedTasks:
            taskAssignment = AssignedTask.objects.get(
                team=team,
                task=t)
            taskAssignment.completedAt = timezone.now()
            taskAssignment.save()

    return "<br/>".join(messages)

class ActionView(View):
    def unfinishedActionBy(self, user):
        """
        Return one of the unfinished actions by the current user, None otherwise
        """
        unfinished = Action.objects \
            .filter(actionevent__author=user) \
            .annotate(
                initcount=Count('actionevent',
                    filter=Q(actionevent__phase=ActionPhase.initiate))) \
            .annotate(allcount=Count('actionevent')) \
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
        state = State.objects.getNewest()
        state.setContext(ActionContext.latests())
        form = MoveInitialForm(state=state, user=request.user)
        return render(request, "game/actionIndex.html", {
            "request": request,
            "form": form,
            "teams": Team.objects.all(),
            "messages": messages.get_messages(request)
        })

    @method_decorator(login_required)
    def post(self, request):
        if not request.user.isOrg():
            raise PermissionDenied("Cannot view the page")
        state = State.objects.getNewest()
        state.setContext(ActionContext.latests())
        form = MoveInitialForm(data=request.POST, state=state, user=request.user)
        if form.is_valid():
            return redirect(reverse('actionInitiate', kwargs={
                                    "moveId": form.cleaned_data['action'].value,
                                    "teamId": form.cleaned_data['team'].id
            }) + '?' + urlencode({"entity": form.cleaned_data['entity']}))
        return render(request, "game/actionIndex.html", {
            "request": request,
            "form": form,
            "teams": Team.objects.all(),
            "messages": messages.get_messages(request)
        })


class ActionInitiateView(ActionView):
    @method_decorator(login_required)
    def get(self, request, teamId, moveId):
        if not request.user.isOrg():
            raise PermissionDenied("Cannot view the page")
        unfinishedAction = self.unfinishedActionBy(request.user)
        if unfinishedAction:
            messages.warning(request, self.unfinishedMessage(unfinishedAction))
            return redirect('actionDiceThrow', actionId=unfinishedAction.id)
        try:
            state = State.objects.getNewest()
            state.setContext(ActionContext.latests())
            formClass = formForActionType(moveId)
            form = formClass(team=teamId, action=moveId, user=request.user, entity=request.GET.get("entity"), state=state)
            return render(request, "game/actionInitiate.html", {
                "request": request,
                "form": form,
                "team": get_object_or_404(Team, pk=teamId),
                "action": ActionType(moveId),
                "messages": messages.get_messages(request)
            })
        except InvalidActionException as e:
            messages.error(request, str(e))
            return redirect("actionIndex")

    @method_decorator(login_required)
    def post(self, request, teamId, moveId):
        if not request.user.isOrg():
            raise PermissionDenied("Cannot view the page")
        state = State.objects.getNewest()
        state.setContext(ActionContext.latests())
        team = get_object_or_404(Team, pk=teamId)
        form = formForActionType(moveId)(data=request.POST.copy(), # copy, so we can change the cancelled field
             state=state, team=teamId, user=request.user)
        try:
            if form.is_valid() and not form.cleaned_data["canceled"]:
                action = buildAction(form.cleaned_data)
                requiresDice = action.requiresDice(state)
                initiateStep = ActionEvent.initiateAction(request.user, action)
                res = initiateStep.applyTo(state)
                if res.success and not requiresDice:
                    commitStep = ActionEvent.commitAction(request.user, action, 0)
                    commitRes = commitStep.applyTo(state)
                    res.append(commitRes)
                message = res.message
                if res.success:
                    message += "<br>" + awardStickers(request, state, team,
                        res.stickers)
                    message += "<br>" + handleNewTasks(request, state, team,
                        res.startedTasks, res.finishedTasks)

                form.data["canceled"] = True
                return render(request, "game/actionConfirm.html", {
                    "request": request,
                    "form": form,
                    "team": team,
                    "action": action,
                    "requiresDice": requiresDice,
                    "moveValid": res.success,
                    "message": message,
                    "messages": messages.get_messages(request)
                })
        except InvalidActionException as e:
            messages.error(request, str(e))
        form.data["canceled"] = False
        return render(request, "game/actionInitiate.html", {
            "request": request,
            "form": form,
            "team": get_object_or_404(Team, pk=teamId),
            "action": ActionType(moveId),
            "messages": messages.get_messages(request)
        })

class ActionConfirmView(ActionView):
    @method_decorator(login_required)
    def post(self, request, teamId, moveId):
        if not request.user.isOrg():
            raise PermissionDenied("Cannot view the page")
        try:
            state = State.objects.getNewest()
            state.setContext(ActionContext.latests())
            team = get_object_or_404(Team, pk=teamId)
            form = formForActionType(moveId)(data=request.POST, state=state, team=teamId, user=request.user)
            if form.is_valid(): # Should be always unless someone plays with API directly
                action = buildAction(form.cleaned_data)
                requiresDice = action.requiresDice(state)
                initiateStep = ActionEvent.initiateAction(request.user, action)
                res = initiateStep.applyTo(state)
                if res.success and not requiresDice:
                    commitStep = ActionEvent.commitAction(request.user, action, 0)
                    commitRes = commitStep.applyTo(state)
                    res.append(commitRes)
                    awardAchievements(request, state, team)
                message = res.message
                if res.success:
                    message += "<br>" + awardStickers(request, state, team,
                        res.stickers, res.success)
                    message += "<br>" + handleNewTasks(request, state, team,
                        res.startedTasks, res.finishedTasks, res.success)

                if not res.success:
                    form.data["canceled"] = True
                    return render(request, "game/actionConfirm.html", {
                        "request": request,
                        "form": form,
                        "team": team,
                        "action": action,
                        "moveValid": res.success,
                        "message": message,
                        "messages": messages.get_messages(request)
                    })
                action.save()
                initiateStep.save()
                if not requiresDice:
                    commitStep.save()
                state.save()
                if requiresDice:
                    messages.success(request,
                        f"Akce {action.description()} započata s efektem: <br/> {message}")
                    return redirect('actionDiceThrow', actionId=action.id)
                messages.success(request,
                        f"Akce {action.description()} provedena s efektem: <br/> {message}")
                return redirect('actionIndex')
        except InvalidActionException as e:
            messages.error(request, str(e))
        return HttpResponse(status=422)

class ActionDiceThrow(ActionView):
    @method_decorator(login_required)
    def get(self, request, actionId):
        if not request.user.isOrg():
            raise PermissionDenied("Cannot view the page")
        action = get_object_or_404(Action, pk=actionId).resolve()
        if self.isFinished(action):
            messages.error(request, "Akce již byla dokončena. Nesnažíte se obnovit načtenou stránku?")
            return redirect('actionIndex')
        state = State.objects.getNewest()
        form = DiceThrowForm(action.dotsRequired(state).keys())
        return self.renderForm(request, action, form)

    def renderForm(self, request, action, form):
        state = State.objects.getNewest()
        teamState = state.teamState(action.team.id)
        diceThrowMessage = action.diceThrowMessage(state)
        return render(request, "game/actionDiceThrow.html", {
            "request": request,
            "form": form,
            "team": action.team,
            "action": action,
            "diceThrowMessage": diceThrowMessage,
            "requiredDices": action.dotsRequired(state),
            "messages": messages.get_messages(request),
            "maxThrows": teamState.resources.get("res-prace") // parameters.DICE_THROW_PRICE
        })

    @method_decorator(login_required)
    def post(self, request, actionId):
        if not request.user.isOrg():
            raise PermissionDenied("Cannot view the page")
        action = get_object_or_404(Action, pk=actionId).resolve()
        if self.isFinished(action):
            messages.error(request, "Akce již byla dokončena. Nesnažíte se obnovit načtenou stránku?")
            return redirect('actionIndex')
        state = State.objects.getNewest()
        form = DiceThrowForm(action.dotsRequired(state).keys(), data=request.POST)
        if not form.is_valid():
            return self.renderForm(request, action, form)
        team = get_object_or_404(Team, pk=action.team.id)
        try:
            state = State.objects.getNewest()
            teamState = state.teamState(action.team.id)
            maxThrowTries = teamState.resources.get("res-prace") // parameters.DICE_THROW_PRICE
            if form.cleaned_data["throwCount"] > maxThrowTries:
                messages.error(request, """
                    Zadali jste více hodů než na kolik má tým nárok. Tým mohl hodit
                    maximálně <b>{}x</b>, hodil však <b>{}x</b>. Pokud to není chyba,
                    je možné, že tým házel zároveň i na jiném stanovišti a tam
                    spotřeboval práci. V tom případě dokončete akci znovu -- jen
                    zadejte maximální počet hodů.""".format(maxThrowTries, form.cleaned_data["throwCount"]))
                return redirect('actionDiceThrow', actionId=action.id)
            if form.cleaned_data["throwCount"] == 0 and form.cleaned_data["dotsCount"] != 0:
                messages.error(request, "Tým neházel, ale přesto má nenulový počet puntíků. Opakujte zadání.")
                return redirect('actionDiceThrow', actionId=action.id)
            if "cancel" in request.POST.get("submit", "") == "cancel":
                step = ActionEvent.cancelAction(request.user, action)
                channel = messages.warning
            else:
                dice = action.context.dies.get(id=form.cleaned_data["dice"])
                requiredDots = action.dotsRequired(state)[dice]
                workConsumed = form.cleaned_data["throwCount"] * parameters.DICE_THROW_PRICE
                if form.cleaned_data["dotsCount"] >= requiredDots:
                    step = ActionEvent.commitAction(request.user, action, workConsumed)
                    channel = messages.success
                else:
                    step = ActionEvent.abandonAction(request.user, action, workConsumed)
                    channel = messages.warning
            res = step.applyTo(state)
            if not res.success:
                messages.error(res.message)
                return redirect('actionDiceThrow', actionId=action.id)
            message = awardStickers(request, state, team, res.stickers, True)
            message += "<br>" + handleNewTasks(request, state, team,
                res.startedTasks, res.finishedTasks, True)
            awardAchievements(request, state, team)
            action.save()
            step.save()
            state.save()
            if len(res.message) > 0:
                channel(request, res.message + "<br>" + message)
            return redirect('actionIndex')
        except InvalidActionException as e:
            messages.error(request, str(e))
            return redirect('actionDiceThrow', actionId=action.id)

    def isFinished(self, action):
        return action.actionevent_set.all().exclude(phase=ActionPhase.initiate).exists()