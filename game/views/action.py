from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.core.exceptions import PermissionDenied

class ActionIndexView(View):
    @method_decorator(login_required)
    def get(self, request):
        if request.user.isPlayer():
            raise PermissionDenied("Cannot view the page")
        return render(request, "game/action.html", {
            "request": request
        })