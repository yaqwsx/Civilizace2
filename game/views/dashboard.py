from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.core.exceptions import PermissionDenied
from game.models import Team

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
        return render(request, 'game/dashboard.html', {
            "request": request,
            "team": team,
            "teams": Team.objects.all()
        })

class DemoView(View):
    def get(self, request, *args, **kwargs):
        return render(request, 'demo.html')