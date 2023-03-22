from typing import Any, List, Optional, Tuple, Dict
from django.shortcuts import get_object_or_404
from django.db.models.functions import Now
from django.db.models.query import QuerySet
from frozendict import frozendict
from rest_framework import viewsets

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from core.models.announcement import Announcement
from core.serializers.team import TeamSerializer
from game.actions.feed import computeFeedRequirements
from game.entities import Entities, Entity, EntityId, Tech, Resource, TeamId, Vyroba, MapTileEntity
from game.gameGlue import serializeEntity, stateSerialize

from rest_framework import serializers

from game.models import DbDelayedEffect, DbEntities, DbState, DbSticker, DbTask, DbTaskAssignment
from game.serializers import DbTaskSerializer, PlayerDbTaskSerializer
from game.state import GameState, TeamState, MapTile, Army

from core.models import User, Team as DbTeam
from game.viewsets.stickers import DbStickerSerializer
from game.viewsets.voucher import DbDelayedEffectSerializer

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
        return self._list("techs")

    @action(detail=False)
    def vyrobas(self, request):
        return self._list("vyrobas")

    @action(detail=False)
    def tiles(self, request):
        return self._list("tiles")

    @action(detail=False)
    def buildings(self, request):
        return self._list("buildings")

    @action(detail=False)
    def dice(self, request):
        return self._list("dice")

    def list(self, request):
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

    @staticmethod
    def serializeArmy(a, reachableTiles):
        return {
            "index": a.index,
            "team": a.team,
            "name": a.name,
            "level": a.level,
            "equipment": a.equipment,
            "boost": a.boost,
            "tile": a.tile.id if a.tile is not None else None,
            "mode": str(a.mode).split(".")[1],
            "goal": str(a.goal).split(".")[1] if a.goal is not None else None,
            "reachableTiles": [t.id for t in reachableTiles] if reachableTiles is not None else None
        }

    @action(detail=True)
    def resources(self, request, pk):
        self.validateAccess(request.user, pk)
        resources = self.getTeamState(pk).resources

        assert all(amount >= 0 for amount in resources.values())
        return Response({res.id: serializeEntity(res, {"available": resources[res]})
                         for res in resources.keys() if resources[res] > 0})

    @action(detail=True)
    def vyrobas(self, request, pk):
        self.validateAccess(request.user, pk)
        teamState, entities = self.getTeamStateAndEntities(pk)
        state = teamState.parent

        vList = list(teamState.vyrobas)
        teamReachableTiles = state.map.getReachableTiles(entities[pk])

        def isTileSuitable(vyroba, tile):
            tileFeatures = set(tile.buildings).union(tile.entity.naturalResources)
            return all(f in tileFeatures for f in vyroba.requiredFeatures)

        def allowed_tiles(vyroba: Vyroba) -> List[EntityId]:
            return [t.id for t in teamReachableTiles if isTileSuitableFor(vyroba, t)]

        vList.sort(key=lambda x: x.id)
        return Response({v.id: serializeEntity(v, {"allowedTiles": allowed_tiles(v)})
                            for v in vList})


    @action(detail=True)
    def buildings(self, request, pk):
        self.validateAccess(request.user, pk)
        teamState, entities = self.getTeamStateAndEntities(pk)

        bList = list(teamState.buildings)
        bList.sort(key=lambda x: x.name)
        return Response({b.id: serializeEntity(b) for b in bList})


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

        def tech_extra_fields(tech):
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

        return Response({tech.id: serializeEntity(tech, tech_extra_fields(tech)) for tech in teamTechs})

    @action(detail=True)
    def tasks(self, request, pk):
        self.validateAccess(request.user, pk)
        team = get_object_or_404(DbTeam.objects.all(), pk=pk)
        if request.user.isOrg:
            taskSet = DbTask.objects.all()
            serializer = DbTaskSerializer
        else:
            taskSet = DbTask.objects.filter(assignments__team=team.pk)
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

        feedRequirements = computeFeedRequirements(state, entities, entities[pk])

        return Response({
            "population": {
                "nospec": teamState.resources[entities["res-obyvatel"]],
                "all": teamState.population
            },
            "work": teamState.work,
            "culture": teamState.culture,
            "worldTurn": state.world.turn,
            "teamTurn": teamState.turn,
            "researchingTechs": [serializeEntity(x) for x in teamState.researching],
            "productions": [
                (r.id, a) for r, a in teamState.resources.items()
                    if r.isProduction and r.id != "res-obyvatel"
            ],
            "storage": [
                (r.id, a) for r, a in teamState.storage.items()
            ],
            "granary": [
                (r.id, a) for r, a in teamState.granary.items() if r.typ[0].id == "typ-jidlo"
            ] + [
                (r.id, a) for r, a in teamState.granary.items() if r.typ[0].id == "typ-luxus"
            ],
            "feeding": {
                "casteCount": feedRequirements.casteCount,
                "tokensPerCaste": feedRequirements.tokensPerCaste,
                "tokensRequired": feedRequirements.tokensRequired,
            },
            "announcements": [
                {
                    "id": a.id,
                    "type": a.typeString(),
                    "content": a.content,
                    "read": False,
                    "appearDatetime": a.appearDatetime
                } for a in self.unreadAnnouncements(request.user, team)
            ],
            "armies": [
                self.serializeArmy(a, None) for a in state.map.getTeamArmies(entities[pk])
            ],
            "techs": list(x.id for x in teamState.techs),
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
                "appearDatetime": a.appearDatetime,
                "readBy": set([x.team.name for x in a.read.all()]) if request.user.isOrg else None
            } for a in Announcement.objects.getTeam(team)
        ])

    @action(detail=True)
    def armies(self, request, pk):
        self.validateAccess(request.user, pk)
        tState, entities = self.getTeamStateAndEntities(pk)
        state = tState.parent
        reachableTiles = state.map.getReachableTiles(entities[pk])

        return Response({a.index: self.serializeArmy(a, reachableTiles)
                            for a in state.map.getTeamArmies(entities[pk])})

    @action(detail=True)
    def stickers(self, request, pk):
        self.validateAccess(request.user, pk)
        stickers = DbSticker.objects.filter(team__id=pk).order_by("-awardedAt")
        return Response(DbStickerSerializer(stickers, many=True).data)

    @action(detail=True)
    def vouchers(self, request, pk):
        self.validateAccess(request.user, pk)
        effects = DbDelayedEffect.objects.filter(team__id=pk).order_by("withdrawn", "-round", "-target")
        return Response(DbDelayedEffectSerializer(effects, many=True).data)


    @action(detail=True)
    def storage(self, request, pk):
        self.validateAccess(request.user, pk)
        storage = self.getTeamState(pk).storage

        return Response({r.id: a for r, a in storage.items() if a > 0})

    @action(detail=True)
    def feeding(self, request, pk):
        self.validateAccess(request.user, pk)
        teamState, entities = self.getTeamStateAndEntities(pk)
        state = teamState.parent
        team = entities[pk]

        return Response(stateSerialize(computeFeedRequirements(state, entities, team)))

    @action(detail=True)
    def tiles(self, request, pk):
        self.validateAccess(request.user, pk)
        tState, entities = self.getTeamStateAndEntities(pk)
        state = tState.parent
        teamE = entities[pk]
        reachableTiles = state.map.getReachableTiles(teamE)

        return Response({t.entity.id: {
            "entity": serializeEntity(t.entity),
            "unfinished": [x.id for x in t.unfinished.get(teamE, [])],
            "buildings": [x.id for x in t.buildings],
            "richness": t.richness
        } for t in reachableTiles})
