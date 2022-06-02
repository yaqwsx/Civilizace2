from typing import Any, Optional, Tuple, Dict
from django.shortcuts import get_object_or_404
from django.db.models.functions import Now
from rest_framework import viewsets

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from core.models.announcement import Announcement
from core.serializers.team import TeamSerializer
from game.entities import Entities, Entity, Tech
from game.gameGlue import serializeEntity

from rest_framework import serializers

from game.models import DbEntities, DbState, DbTask, DbTaskAssignment
from game.serializers import DbTaskSerializer, PlayerDbTaskSerializer
from game.state import GameState, TeamState

from core.models import Team as DbTeam

from .permissions import IsOrg

class ChangeTaskSerializer(serializers.Serializer):
    tech = serializers.CharField()
    newTask = serializers.CharField(allow_blank=True, allow_null=True)

class EntityViewSet(viewsets.ViewSet):
    permission_classes = (IsAuthenticated,)

    @action(detail=False)
    def resources(self, request):
        return self._list("resources")

    @action(detail=False)
    def techs(self, request):
        if not request.user.isOrg:
            raise PermissionDenied()
        return self._list("techs")

    @action(detail=False)
    def vyrobas(self, request):
        if not request.user.isOrg:
            raise PermissionDenied()
        return self._list("vyrobas")

    def list(self, request):
        if not request.user.isOrg:
            raise PermissionDenied()
        return self._list("all")

    def _list(self, entityType):
        entities = DbEntities.objects.get_revision()[1]
        subset = getattr(entities, entityType)
        return Response({id: serializeEntity(e) for id, e in subset.items()})

class TeamViewSet(viewsets.ViewSet):
    permission_classes = (IsAuthenticated, )

    def validateAccess(self, user, teamId):
        if not user.isOrg and user.team.id != teamId:
            raise PermissionDenied("Nedovolený přístup")

    def getTeamState(self, teamId: str) -> TeamState:
        return self.getTeamStateAndEntities(teamId)[0]

    def getTeamStateAndEntities(self, teamId: str):
        dbState = DbState.objects.latest("id")
        state = dbState.toIr()
        entities = dbState.entities
        return state.teamStates[entities[teamId]], entities

    def unreadAnnouncements(self, user, team):
        if user.isOrg:
            return Announcement.objects.getTeamUnread(team)
        return Announcement.objects.getUnread(user)

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
        self.validateAccess(request.user, pk)
        entities = DbEntities.objects.get_revision()[1]
        resources = self.getTeamState(pk).resources

        def enrich(entity: Entity) -> Dict[str, Any]:
            return {"available": resources.get(entity.id, 0)}

        return Response({id: serializeEntity(e, enrich) for id, e in entities.resources.items()})

    @action(detail=True)
    def vyrobas(self, request, pk):
        self.validateAccess(request.user, pk)
        vList = list(self.getTeamState(pk).vyrobas)
        vList.sort(key=lambda x: x.id)
        return Response({e.id: serializeEntity(e) for e in vList})


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
                try:
                    assignment = DbTaskAssignment.objects\
                        .get(team=team, techId=tech.id, finishedAt=None)
                except DbTaskAssignment.DoesNotExist:
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
        self.validateAccess(request.user, pk)
        team = get_object_or_404(DbTeam.objects.all(), pk=pk)
        if request.user.isOrg:
            taskSet = DbTask.objects.all()
            serializer = DbTaskSerializer
        else:
            taskSet = DbTask.objects.filter(assignments__team=team.pk, abandoned=False)
            serializer = PlayerDbTaskSerializer

        return Response({t.id: serializer(t).data for t in taskSet})

    @action(detail=True)
    def work(self, request, pk):
        self.validateAccess(request.user, pk)
        state = self.getTeamState(pk)

        return Response({
            "work": state.work
        })

    @action(detail=True, methods=["POST"])
    def changetask(self, request, pk):
        self.validateAccess(request.user, pk)
        team = get_object_or_404(DbTeam.objects.all(), pk=pk)

        deserializer = ChangeTaskSerializer(data=request.data)
        deserializer.is_valid(raise_exception=True)
        data = deserializer.validated_data

        try:
            assignment = DbTaskAssignment.objects\
                            .get(team=team, techId=data["tech"], finishedAt=None)
            assignment.finishedAt = Now()
            assignment.abandoned = True
            assignment.save()
        except DbTaskAssignment.DoesNotExist:
            pass

        if data["newTask"]:
            DbTaskAssignment.objects.create(
                team=team,
                task=get_object_or_404(DbTask.objects.all(), pk=data["newTask"]),
                techId=data["tech"])
        return Response({})

    @action(detail=True)
    def dashboard(self, request, pk):
        self.validateAccess(request.user, pk)
        team = get_object_or_404(DbTeam.objects.all(), pk=pk)

        dbState = DbState.objects.latest("id")
        state = dbState.toIr()
        entities = dbState.entities
        teamState = state.teamStates[entities[pk]]

        return Response({
            "population": {
                "spec": "TBA",
                "all": "TBA"
            },
            "work": teamState.work,
            "turn": state.turn,
            "researchingTechs": [serializeEntity(x) for x in teamState.researching],
            "productions": [
                (r.id, a) for r, a in teamState.resources.items()
                    if r.isProduction
            ],
            "storage": [
                (r.id, a) for r, a in teamState.storage.items()
            ],
            "announcements": [
                {
                    "id": a.id,
                    "type": a.typeString(),
                    "content": a.content,
                    "read": False,
                    "datetime": a.appearDatetime
                } for a in self.unreadAnnouncements(request.user, team)
            ]
        })

    @action(detail=True)
    def announcements(self, request, pk):
        self.validateAccess(request.user, pk)
        team = get_object_or_404(DbTeam.objects.all(), pk=pk)
        return Response([
            {
                "id": a.id,
                "type": a.typeString(),
                "content": a.content,
                "read": request.user in a.read.all(),
                "datetime": a.appearDatetime,
                "readBy": set([x.team.name for x in a.read.all()]) if request.user.isOrg else None
            } for a in Announcement.objects.getTeam(team)
        ])

    @action(detail=True)
    def armies(self, request, pk):
        self.validateAccess(request.user, pk)

        state = self.getTeamState(pk)
        return Response({a.prestige: {
                "prestige": a.prestige,
                "equipment": a.equipment,
                "boost": a.boost,
                "tile": a.tile.id if a.tile is not None else None,
                "state": str(a.state).split(".")[1],
                "goal": str(a.goal).split(".")[1] if a.goal is not None else None,
            } for a in state.armies.values()})
