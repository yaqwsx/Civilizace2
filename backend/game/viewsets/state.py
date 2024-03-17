from rest_framework import viewsets
from game.models import DbState
from game.serializers import Serializer
from game.viewsets.permissions import IsOrg
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.decorators import action


class StateViewSet(viewsets.ViewSet):
    permission_classes = (IsAuthenticated, IsOrg)

    @action(detail=False)
    def latest(self, request: Request) -> Response:
        state = DbState.get_latest()
        ir = state.toIr()
        return Response(Serializer().serialize(ir))
