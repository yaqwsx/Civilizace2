from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from game.models import DbState
from game.serializers import Serializer
from game.viewsets.permissions import IsOrg


class MapViewSet(viewsets.ViewSet):
    permission_classes = (IsAuthenticated, IsOrg)

    def list(self, request):
        dbState: DbState = DbState.get_latest()
        entities = dbState.entities
        state = dbState.toIr()
        tiles = state.map.tiles

        tilesRep = [Serializer().serialize(tiles[i]) for i in range(state.map.size)]
        for i in range(state.map.size):
            tilesRep[i]["name"] = tiles[i].entity.name
        return Response(tilesRep)
