from django.views import View
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

class DashboardView(View):
    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        print(request.user)
        return render(request, 'game/dashboard.html', {
            "user": request.user
        })

class DemoView(View):
    def get(self, request, *args, **kwargs):
        return render(request, 'demo.html')