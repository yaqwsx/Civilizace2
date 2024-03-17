from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from game.models import DbState
from game.serializers import Serializer
from game.viewsets.permissions import IsOrg


class ArmiesViewSet(viewsets.ViewSet):
    permission_classes = (IsAuthenticated, IsOrg)

    def list(self, request):
        dbState = DbState.get_latest()
        entities = dbState.entities
        state = dbState.toIr()

        armiesResp = [Serializer().serialize(a) for a in state.map.armies]
        for a, original in zip(armiesResp, state.map.armies):
            a["tile"] = original.currentTile.id if original.currentTile else None
        return Response(armiesResp)
