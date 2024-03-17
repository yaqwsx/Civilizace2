from typing import Callable, Mapping

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from game.entities import Entities, Entity, EntityId
from game.models import DbEntities
from game.serializers import Serializer


class EntityViewSet(viewsets.ViewSet):
    permission_classes = (IsAuthenticated,)

    @action(detail=False)
    def resources(self, request: Request) -> Response:
        return self._list(lambda e: e.resources)

    @action(detail=False)
    def techs(self, request: Request) -> Response:
        return self._list(lambda e: e.techs)

    @action(detail=False)
    def vyrobas(self, request: Request) -> Response:
        return self._list(lambda e: e.vyrobas)

    @action(detail=False)
    def tiles(self, request: Request) -> Response:
        return self._list(lambda e: e.tiles)

    @action(detail=False)
    def buildings(self, request: Request) -> Response:
        return self._list(lambda e: e.buildings)

    @action(detail=False)
    def building_upgrades(self, request: Request) -> Response:
        return self._list(lambda e: e.building_upgrades)

    @action(detail=False)
    def team_attributes(self, request: Request) -> Response:
        return self._list(lambda e: e.team_attributes)

    @action(detail=False)
    def team_groups(self, request: Request) -> Response:
        return self._list(lambda e: e.team_groups)

    @action(detail=False)
    def dice(self, request: Request) -> Response:
        return self._list(lambda e: e.dice)

    def list(self, request: Request) -> Response:
        return self._list(lambda e: e.all)

    def _list(
        self, entitySelector: Callable[[Entities], Mapping[EntityId, Entity]]
    ) -> Response:
        entities = DbEntities.objects.get_revision()[1]
        return Response(
            {
                e.id: Serializer().serialize_entity(e)
                for e in entitySelector(entities).values()
            }
        )
