from rest_framework import viewsets
from game.gameGlue import stateSerialize
from game.models import DbState
from game.state import GameState
from game.viewsets.permissions import IsOrg
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action


class PlagueViewSet(viewsets.ViewSet):
    # permission_classes = (IsAuthenticated, IsOrg)

    def list(self, request):
        return Response([])

