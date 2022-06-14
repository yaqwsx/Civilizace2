from rest_framework import viewsets
from game.gameGlue import stateSerialize
from game.models import DbEntities, DbState
from game.state import GameState
from game.viewsets.permissions import IsOrg
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action


class PlagueViewSet(viewsets.ViewSet):
    # permission_classes = (IsAuthenticated, IsOrg)

    def list(self, request):
        entityRevision, entities = DbEntities.objects.get_revision()
        return Response({k: v.word for k, v in entities.plague.slugToWordMapping.items()})

