from game.models.messageBoard import Message
from django.views import View
from django import forms
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, reverse
from game.models.generationTick import (
    GenerationTickSettings, ExpectedGeneration,
    updateGeneration, getExpectedGeneration, getGenerationSettings)
from django.contrib import messages
from django.utils import timezone

from datetime import timedelta, datetime

from game.models.users import User
from game.models.state import State
from game.models.actionBase import ActionEvent
from game.models.actions.worldActions import NextGenerationAction


class GenerationForm(forms.Form):
    renew = forms.BooleanField(required=False, label="Automaticky se obnovují generace")
    period = forms.IntegerField(required=True, min_value=1, label="Perioda generace (min)")

class GenerationConfigView(View):
    @method_decorator(login_required)
    def get(self, request):
        if not request.user.isOrg():
            raise PermissionDenied("Cannot view the page")
        p = getGenerationSettings()
        form = GenerationForm(initial={
            "renew": p.renew,
            "period": p.period / timedelta(minutes=1)
        })
        return render(request, "game/generationSettings.html", {
            "request": request,
            "form": form,
            "messages": messages.get_messages(request)
        })

    @method_decorator(login_required)
    def post(self, request):
        if not request.user.isOrg():
            raise PermissionDenied("Cannot view the page")
        if "reset" in request.POST or "start" in request.POST:
            return self.start(request)
        if "stop" in request.POST:
            return self.stop(request)
        form = GenerationForm(request.POST)
        if form.is_valid():
            p = getGenerationSettings()
            p.period =  timedelta(minutes=form.cleaned_data["period"])
            p.renew = form.cleaned_data["renew"]
            p.save()
            messages.info(request, "Parametry automatického čítače generací změněny")
            return redirect(reverse("generationConfig"))
        else:
            return render(request, "game/generationSettings.html", {
                "request": request,
                "form": form,
                "messages": messages.get_messages(request)
            })

    def start(self, request):
        g = getExpectedGeneration()
        s = getGenerationSettings()
        g.generationDue = timezone.now() + s.period
        g.save()
        messages.info(request, f"Čítač generací byl nastaven na {s.period / timedelta(minutes=1)} minut")
        return redirect(reverse("generationConfig"))

    def stop(self, request):
        g = getExpectedGeneration()
        g.generationDue = None
        g.save()
        messages.info(request, "Čítač generací je zastaven")
        return redirect(reverse("generationConfig"))

class GenerationInfo(View):
    def get(self, request):
        expGeneration = getExpectedGeneration()
        return JsonResponse({
            "serverTime": timezone.now(),
            "nextGenerationEnd": expGeneration.generationDue,
            "generationNum": expGeneration.seq
        })

class GenerationCountDownView(View):
    def get(self, request):
        expGeneration = getExpectedGeneration()
        return render(request, "game/generationCountdown.html", {
            "request": request,
            "serverTime": timezone.now(),
            "nextGenerationEnd": expGeneration.generationDue,
            "generation": State.objects.getNewest().worldState.generation
        })


class AnnouncementView(View):
    def get(self, request):
        announcements = [m for m in Message.objects.order_by("-appearDateTime").all() if m.isPublic()]
        return render(request, "game/announcements.html", {
            "request": request,
            "announcements": announcements[:5]
        })
