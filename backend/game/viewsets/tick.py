from rest_framework import viewsets
from rest_framework.response import Response

from game.middleware import updateScheduledActions, updateTurn

class TickViewSet(viewsets.ViewSet):
    def list(self, request):
        updateTurn()
        updateScheduledActions()
        return Response({"status": "OK"})
