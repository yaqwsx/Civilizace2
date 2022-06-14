import io
from django.shortcuts import get_object_or_404
from django.db import transaction
from rest_framework import serializers, viewsets, mixins
from rest_framework.decorators import action
from rest_framework.exceptions import APIException
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
        return Response(armiesResp)
