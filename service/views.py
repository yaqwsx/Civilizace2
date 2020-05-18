import tempfile
import io
from django.http import FileResponse
from django.shortcuts import render
from django.views import View
from game.data.update import Update, UpdateError

from service.plotting import tech

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


class DownloadTechTree(View):
    def get(self, request):
        with tempfile.TemporaryDirectory() as tmpdirname:
            builder = tech.TechBuilder(tmpdirname)
            builder.generateTechLabels()
            builder.generateFullGraph()
            with open(builder.fullGraphFile(), "rb") as f:
                graphPdf = io.BytesIO(f.read())
                graphPdf.seek(0)
                return FileResponse(graphPdf, filename='techstrom.pdf')

