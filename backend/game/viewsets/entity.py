from typing import Tuple
from django.shortcuts import get_object_or_404
from rest_framework import viewsets

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from core.serializers.team import TeamSerializer
from game.entities import Entities, Tech
from game.gameGlue import serializeEntity

from game.models import DbEntities, DbState, DbTaskAssignment
from game.state import TeamState

from core.models import Team as DbTeam

from .permissions import IsOrg

class EntityViewSet(viewsets.ViewSet):
    permission_classes = (IsAuthenticated, IsOrg)

    @action(detail=False)
    def resources(self, request):
        return self._list("resources")

    @action(detail=False)
    def techs(self, request):
        return self._list("techs")

    @action(detail=False)
    def vyrobas(self, request):
        return self._list("vyrobas")

    def list(self, request):
        return self._list("all")

    def _list(self, entityType):
        entities = DbEntities.objects.get_revision()
        subset = getattr(entities, entityType)
        return Response({id: serializeEntity(e) for id, e in subset.items()})

class TeamViewSet(viewsets.ViewSet):
    permission_classes = (IsAuthenticated, )

    def validateAccess(self, user, teamId):
        if not user.isOrg and user.team.id != teamId:
            raise PermissionDenied("Nedovolený přístup")

    def getTeamState(self, teamId: str) -> TeamState:
        dbState = DbState.objects.latest("id")
        state = dbState.toIr()
        entities = dbState.entities
        return state.teamStates[entities[teamId]]

    def list(self, request):
        if not request.user.isOrg:
            raise PermissionDenied("Nedovolený přístup")
        serializer = TeamSerializer(DbTeam.objects.all(), many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk):
        self.validateAccess(request.user, pk)

        t = get_object_or_404(DbTeam.objects.filter(visible=True), pk=pk)
        serializer = TeamSerializer(t)
        return Response(serializer.data)

    @action(detail=True)
    def resources(self, request, pk):
        raise NotImplementedError("TBA")

    @action(detail=True)
    def techs(self, request, pk):
        self.validateAccess(request.user, pk)
        team = get_object_or_404(DbTeam.objects.all(), pk=pk)

        state = self.getTeamState(pk)

        teamTechs = set()
        teamTechs.update(state.techs)
        teamTechs.update(state.researching)
        for t in state.techs:
            teamTechs.update([x for x, _ in t.unlocks if isinstance(x, Tech)])

        def enrich(tech):
            if tech in state.techs:
                return { "status": "owned" }
            if tech in state.researching:
                assignment = DbTaskAssignment.objects\
                    .get(team=team, techId=tech, finishedAt=None)
                if assignment is None:
                    return { "status": "researching" }
                task = assignment.task
                return {
                    "status": "researching",
                    "assignedTask": {
                        "id": task.id,
                        "name": task.name,
                        "teamDescription": task.teamDescription,
                        "orgDescription": task.orgDescription,
                        "capacity": task.capacity,
                        "occupiedCount": DbTaskAssignment.objects.filter(task=task).count()
                    }
                }
            return { "status": "available" }

        return Response({t.id: serializeEntity(t, enrich) for t in teamTechs})

    @action(detail=True)
    def tasks(self, request, pk):
        raise NotImplementedError("TBA")


