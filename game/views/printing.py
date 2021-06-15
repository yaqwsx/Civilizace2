from django.views import View
from django.utils.decorators import method_decorator
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from ipware import get_client_ip

from game.models.printing import Printer
from game.models.stickers import Sticker

import requests
import io

CLIENT_PORT = 5000

@method_decorator(csrf_exempt, name='dispatch')
class PrintersView(View):
    def post(self, request):
        name = request.POST["name"]
        clientIp, _ = get_client_ip(request)
        if clientIp is None:
            return HttpResponse("Cannot trace client", status=403)
        Printer.objects.update_or_create(name=name, defaults={
            "address": clientIp,
            "registeredAt": timezone.now()
        })
        return HttpResponse("")

    @method_decorator(login_required)
    def get(self, request):
        if not request.user.isOrg():
            raise PermissionDenied("Cannot view the page")
        Printer.objects.prune()
        return JsonResponse({"printers": [{
            "name": p.name,
            "id": p.pk,
            "address": p.address
        } for p in Printer.objects.all()]})

@method_decorator(csrf_exempt, name='dispatch')
class PrintStickerView(View):
    @method_decorator(login_required)
    def post(self, request, printerId, stickerId):
        if not request.user.isOrg():
            raise PermissionDenied("Cannot view the page")
        Printer.objects.prune()
        printer = Printer.objects.get(pk=printerId)
        if printer is None:
            return HttpResponse("Taková tiskárna neexistuje", status=404)
        sticker = Sticker.objects.get(pk=stickerId)
        if sticker is None:
            return HttpResponse("Taková samolepka neexistuje", status=404)

        try:
            printerUrl = f"http://{printer.address}:{CLIENT_PORT}/print"
            r = requests.post(printerUrl, files={
                "image": io.BytesIO(sticker.getImage())
            })
            if r.status_code != 200:
                return HttpResponse(r.text, 403)
        except Exception as e:
            return HttpResponse(str(e), 403)
        return HttpResponse("")