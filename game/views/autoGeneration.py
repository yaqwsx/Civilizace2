from django.views import View
from django import forms
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, reverse
from game.models.generationTick import GenerationTick
from django.contrib import messages

from game.models.users import User
from game.models.state import State
from game.models.actionBase import ActionStep
from game.models.actionMoves.worldActions import NextGenerationAction

def getParameters():
    return GenerationTick.objects.get_or_create(id=1)[0]

class GenerationForm(forms.Form):
    running = forms.BooleanField(required=False, label="Běží časovač")
    period = forms.IntegerField(required=True, min_value=1, label="Perioda (min)")
    forceUpdate = forms.BooleanField(required=False, label="Resetovat aktuálně běžící časovač")

class GenerationConfigView(View):
    @method_decorator(login_required)
    def get(self, request):
        p = getParameters()
        form = GenerationForm(initial={
            "running": p.running,
            "period": p.period / 60,
            "forceUpdate": False
        })
        return render(request, "game/generationSettings.html", {
            "request": request,
            "form": form,
            "messages": messages.get_messages(request)
        })

    @method_decorator(login_required)
    def post(self, request):
        form = GenerationForm(request.POST)
        if form.is_valid():
            p = getParameters()
            p.running = form.cleaned_data["running"]
            p.period = form.cleaned_data["period"] * 60
            p.forceUpdate = form.cleaned_data["forceUpdate"]
            p.save()
            messages.info(request, "Parametry automatického čítače generací změněny")
            return redirect(reverse("generationConfig"))
        else:
            return render(request, "game/generationSettings.html", {
                "request": request,
                "form": form,
                "messages": messages.get_messages(request)
            })

@method_decorator(csrf_exempt, name='dispatch')
class GenerationParameters(View):
    def get(self, request):
        p = getParameters()
        data = {
            'running': p.running,
            'period': p.period,
            'forceUpdate': p.forceUpdate
        }
        return JsonResponse(data)

    def post(self, request):
        p = getParameters()
        p.forceUpdate = False
        p.save()
        return HttpResponse()

class GenerationCountDownView(View):
    def get(self, request):
        return render(request, "game/generationCountdown.html", {
            "request": request,
            "params": getParameters(),
            "generation": State.objects.getNewest().worldState.generation
        })

    def post(self, request):
        state = State.objects.getNewest()
        action = NextGenerationAction.build({
            "team": None,
            "action": NextGenerationAction.CiviMeta.move,
        })
        initiateStep = ActionStep.initiateAction(None, action)
        initiateStep.applyTo(state)
        user = User.objects.get(username="honza")
        commitStep = ActionStep.commitAction(user, action, 0)
        commitStep.applyTo(state)
        action.save()
        initiateStep.save()
        commitStep.save()
        state.save()

        return redirect(reverse("generationCountdown"))

