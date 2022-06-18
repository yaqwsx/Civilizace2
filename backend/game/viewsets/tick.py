from rest_framework import viewsets
from rest_framework.response import Response

from game.middleware import updateDelayedEffects, updatePlague, updateTurn

class TickViewSet(viewsets.ViewSet):
    def list(self, request):
        updateTurn()
        updateDelayedEffects()
        updatePlague()
        return Response({"status": "OK"})
