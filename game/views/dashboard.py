from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from django.contrib import messages
from game.models.users import Team
from game.models.state import State
from game.models.messageBoard import Message


class DashboardIndexView(View):
    @method_decorator(login_required)
    def get(self, request):
        if request.user.isOrg():
            firstTeam = Team.objects.all().first()
            return redirect("dashboardStat", teamId=firstTeam.pk)
        return redirect("dashboardStat", teamId=request.user.team().pk)


class DashboardStatView(View):
    @method_decorator(login_required)
    def get(self, request, teamId):
        user = request.user
        if user.isPlayer() and user.team().id != teamId:
            raise PermissionDenied("Cannot view the page")

        team = get_object_or_404(Team, pk=teamId)
        state = State.objects.getNewest()
        teamState = state.teamState(teamId)
        worldState = state.worldState

        boardMessages = Message.objects.all() \
            .filter(appearDateTime__lte=timezone.now(),
                    messagestatus__team=team.id,
                    messagestatus__visible=True,
                    messagestatus__read=False) \
            .order_by('-appearDateTime')

        return render(request, 'game/dashBoardIndex.html', {
            "request": request,
            "team": team,
            "teams": Team.objects.all(),
            "state": state,
            "teamState": teamState,
            "worldState": worldState,
            "boardMessages": boardMessages,
            "messages": messages.get_messages(request)
        })

class DashboardMessageView(View):
    @method_decorator(login_required)
    def get(self, request, teamId):
        user = request.user
        if user.isPlayer() and user.team().id != teamId:
            raise PermissionDenied("Cannot view the page")
        team = get_object_or_404(Team, pk=teamId)
        boardMessages = Message.objects.all() \
            .filter(appearDateTime__lte=timezone.now(),
                    messagestatus__team=team.id,
                    messagestatus__visible=True) \
            .order_by('-appearDateTime')
        return render(request, 'game/dashBoardMessages.html', {
            "request": request,
            "team": team,
            "teams": Team.objects.all(),
            "boardMessages": boardMessages,
            "messages": messages.get_messages(request)
        })

class DemoView(View):
    def get(self, request, *args, **kwargs):
        return render(request, 'demo.html')