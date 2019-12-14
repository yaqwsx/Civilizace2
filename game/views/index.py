from django.views import View
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

class IndexView(View):
    @method_decorator(login_required)
    def get(self, request):
        # Redirect users based on their role:
        if request.user.isATeam():
            return redirect("dashboardIndex")
        if request.user.isBTeam():
            return redirect("dashboardIndex")
        return redirect("dashboardIndex")