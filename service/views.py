from django.shortcuts import render
from django.views import View
from game.data.update import Update, UpdateError

# Create your views here.

class ValidateEntities(View):
    def get(self, request):
        return render(request, "service/validateEntity.html", {
            "request": request,
            "validated": False
        })

    def post(self, request):
        updater = Update()
        updater.googleAsSource()

        try:
            updater.update()
            warnings = None
        except UpdateError as e:
            warnings = e.warnings

        return render(request, "service/validateEntity.html", {
            "request": request,
            "validated": True,
            "warnings": warnings
        })



