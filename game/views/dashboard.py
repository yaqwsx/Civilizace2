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
            return self.renderOtherTeam(request, user.team().id, teamId)
        return self.renderMyTeam(request, teamId)

    def renderMyTeam(self, request, teamId):
        team = get_object_or_404(Team, pk=teamId)
        state = State.objects.getNewest()
        teamState = state.teamState(teamId)
        worldState = state.worldState
        foodSupplyStats = teamState.foodSupply.getMissingItems(
            worldState.getCastes(),
            teamState.resources.getAmount("res-populace"),
            worldState.foodValue
        )
        foodSupplySurplus = -foodSupplyStats[-1][3]
        foodSupplyTokens = foodSupplyStats[-1][4]

        boardMessages = Message.objects.all() \
            .filter(appearDateTime__lte=timezone.now(),
                    messagestatus__team=team.id,
                    messagestatus__visible=True,
                    messagestatus__read=False) \
            .order_by('-appearDateTime')

        return render(request, 'game/dashBoardIndex.html', {
            "request": request,
            "myTeam": team,
            "targetTeam": team,
            "teams": Team.objects.all(),
            "state": state,
            "teamState": teamState,
            "worldState": worldState,
            "boardMessages": boardMessages,
            "messages": messages.get_messages(request),
            "foodSupplyStats": foodSupplyStats,
            "foodSupplyTokens": foodSupplyTokens,
            "foodSupplySurplus": foodSupplySurplus
        })

    def renderOtherTeam(self, request, myTeamId, otherTeamId):
        myTeam = get_object_or_404(Team, pk=myTeamId)
        otherTeam = get_object_or_404(Team, pk=otherTeamId)
        state = State.objects.getNewest()
        myTeamState = state.teamState(myTeamId)
        otherTeamState = state.teamState(otherTeamId)
        worldState = state.worldState
        return render(request, 'game/dashBoardIndexOther.html', {
            "request": request,
            "myTeam": myTeam,
            "targetTeam": otherTeam,
            "teams": Team.objects.all(),
            "state": state,
            "myTeamState": myTeamState,
            "otherTeamState": otherTeamState,
            "worldState": worldState,
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
            "myTeam": team,
            "targetTeam": team,
            "teams": Team.objects.all(),
            "boardMessages": boardMessages,
            "messages": messages.get_messages(request)
        })

class DashboardTasksView(View):
    @method_decorator(login_required)
    def get(self, request, teamId):
        user = request.user
        if user.isPlayer() and user.team().id != teamId:
            raise PermissionDenied("Cannot view the page")
        team = get_object_or_404(Team, pk=teamId)
        return render(request, 'game/dashBoardTasks.html', {
            "request": request,
            "myTeam": team,
            "targetTeam": team,
            "teams": Team.objects.all(),
            "messages": messages.get_messages(request)
        })

class DashboardStickersView(View):
    @method_decorator(login_required)
    def get(self, request, teamId):
        user = request.user
        if user.isPlayer() and user.team().id != teamId:
            raise PermissionDenied("Cannot view the page")
        team = get_object_or_404(Team, pk=teamId)
        return render(request, 'game/dashBoardStickers.html', {
            "request": request,
            "myTeam": team,
            "targetTeam": team,
            "teams": Team.objects.all(),
            "teamStickers": team.sticker_set.all(),
            "messages": messages.get_messages(request)
        })

class DemoView(View):
    def get(self, request, *args, **kwargs):
        return render(request, 'demo.html')