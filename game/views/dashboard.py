from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from django.contrib import messages
from django.db.models import Exists, OuterRef, Count
from game.models.users import Team
from game.models.state import IslandState, State
from game.models.messageBoard import Message, MessageRead


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
            teamState.resources.get("res-populace"),
            worldState.foodValue
        )
        foodSupplySurplus = -foodSupplyStats[-1][3]
        foodSupplyTokens = foodSupplyStats[-1][4]

        if request.user.isOrg():
            boardMessages = []
        else:
            boardMessages = Message.objects.all() \
                .filter(appearDateTime__lte=timezone.now(),
                        messagestatus__team=team.id,
                        messagestatus__visible=True) \
                .filter(~Exists(
                    MessageRead.objects.filter(
                        user=request.user,
                        message=OuterRef('pk')))) \
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
        if not user.isOrg():
            raise PermissionDenied("Cannot view the page")
        team = get_object_or_404(Team, pk=teamId)
        return render(request, 'game/dashBoardStickers.html', {
            "user": user,
            "request": request,
            "myTeam": team,
            "targetTeam": team,
            "teams": Team.objects.all(),
            "teamStickers": team.sticker_set.order_by('awardedAt').all(),
            "messages": messages.get_messages(request)
        })

def islandKnownBy(islandId, teamStates):
    """
    Return a list of all teams that know the island
    """
    return [t.team for t in teamStates if islandId in t.exploredIslandsList]

class DashboardIslandsView(View):
    @method_decorator(login_required)
    def get(self, request, teamId):
        user = request.user
        if user.isPlayer() and user.team().id != teamId:
            raise PermissionDenied("Cannot view the page")
        team = get_object_or_404(Team, pk=teamId)
        state = State.objects.getNewest()
        teamState = state.teamState(team)
        ownedIslands = list(filter(lambda x: x.owner == team, state.islandStates.all()))
        ownedIslands.sort(key=lambda x: x.island.label)
        knownIslands = [{
            "state": x,
            "knownBy": islandKnownBy(x.island.id, state.teamStates.all())}
                for x in state.islandStates.all()
                if x.island.id in teamState.exploredIslandsList]
        knownIslands.sort(key=lambda x: x["state"].island.label)
        return render(request, 'game/dashBoardIslands.html', {
            "user": user,
            "request": request,
            "myTeam": team,
            "targetTeam": team,
            "teams": Team.objects.all(),
            "ownedIslands": ownedIslands,
            "knownIslands": knownIslands,
            "messages": messages.get_messages(request)
        })


class DemoView(View):
    def get(self, request, *args, **kwargs):
        return render(request, 'demo.html')