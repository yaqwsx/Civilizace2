from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from game.gameGlue import stateSerialize

from game.models import DbState
from game.viewsets.permissions import IsOrg


class ArmiesViewSet(viewsets.ViewSet):
    permission_classes = (IsAuthenticated, IsOrg)

    def list(self, request):
        dbState = DbState.objects.latest()
        entities = dbState.entities
        state = dbState.toIr()

        armiesResp = [stateSerialize(a) for a in state.map.armies]
        for a, original in zip(armiesResp, state.map.armies):
            a["tile"] = original.currentTile.id if original.currentTile else None
        return Response(armiesResp)
