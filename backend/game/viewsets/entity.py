from typing import Any, List, Tuple, Dict
from django.shortcuts import get_object_or_404
from django.db.models.query import QuerySet
from django.utils import timezone
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
from game.entities import Entities, Entity, EntityId, Tech, Vyroba
from game.gameGlue import serializeEntity, stateSerialize

from rest_framework import serializers

from game.models import DbEntities, DbState, DbSticker, DbTask, DbTaskAssignment
from game.serializers import DbTaskSerializer, PlayerDbTaskSerializer
from game.state import TeamState, MapTile, Army

from core.models import User, Team
from game.viewsets.stickers import DbStickerSerializer


TeamId = str  # intentionally left weak


class ChangeTaskSerializer(serializers.Serializer):
    tech = serializers.CharField()
    newTask = serializers.CharField(allow_blank=True, allow_null=True)


class EntityViewSet(viewsets.ViewSet):
    permission_classes = (IsAuthenticated,)

    @action(detail=False)
    def resources(self, request: Request) -> Response:
        return self._list("resources")

    @action(detail=False)
    def techs(self, request: Request) -> Response:
        return self._list("techs")

    @action(detail=False)
    def vyrobas(self, request: Request) -> Response:
        return self._list("vyrobas")

    @action(detail=False)
    def tiles(self, request: Request) -> Response:
        return self._list("tiles")

    @action(detail=False)
    def buildings(self, request: Request) -> Response:
        return self._list("buildings")

    @action(detail=False)
    def dice(self, request: Request) -> Response:
        return self._list("dice")

    def list(self, request: Request) -> Response:
        return self._list("all")

    def _list(self, entityType: str) -> Response:
        entities = DbEntities.objects.get_revision()[1]
        subset: frozendict[EntityId, Entity] = getattr(entities, entityType)
        assert isinstance(subset, frozendict)
        return Response({e.id: serializeEntity(e) for e in subset.values()})


class TeamViewSet(viewsets.ViewSet):
    permission_classes = (IsAuthenticated,)

    def validateAccess(self, user: User, teamId: TeamId) -> None:
        if not user.isOrg:
            assert user.team is not None
            if user.team.id != teamId:
                raise PermissionDenied("Nedovolený přístup")

    def getTeamState(self, teamId: TeamId) -> TeamState:
        return self.getTeamStateAndEntities(teamId)[0]

    def getTeamStateAndEntities(self, teamId: TeamId) -> Tuple[TeamState, Entities]:
        dbState: DbState = DbState.objects.latest("id")
        state = dbState.toIr()
        entities = dbState.entities
        team = entities.teams[teamId]
        return state.teamStates[team], entities

    def unreadAnnouncements(self, user: User, team: Team) -> QuerySet[Announcement]:
        if user.isOrg:
            return Announcement.objects.getTeamUnread(team)
        return Announcement.objects.getUnread(user)

    def list(self, request):
        if not request.user.isOrg:
            raise PermissionDenied("Nedovolený přístup")
        return Response(TeamSerializer(Team.objects.all(), many=True).data)

    def retrieve(self, request: Request, pk: TeamId) -> Response:
        self.validateAccess(request.user, pk)

        t = get_object_or_404(Team.objects.filter(visible=True), pk=pk)
        return Response(TeamSerializer(t).data)

    @staticmethod
    def serializeArmy(a: Army, reachableTiles) -> Dict[str, Any]:
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
            "reachableTiles": [t.id for t in reachableTiles]
            if reachableTiles is not None
            else None,
        }

    @action(detail=True)
    def resources(self, request: Request, pk: TeamId) -> Response:
        self.validateAccess(request.user, pk)
        resources = self.getTeamState(pk).resources

        assert all(amount >= 0 for amount in resources.values())
        return Response(
            {
                res.id: serializeEntity(res, {"available": resources[res]})
                for res in resources.keys()
                if resources[res] > 0
            }
        )

    @action(detail=True)
    def vyrobas(self, request: Request, pk: TeamId) -> Response:
        self.validateAccess(request.user, pk)
        teamState, entities = self.getTeamStateAndEntities(pk)
        state = teamState.parent

        vList = list(teamState.vyrobas)
        teamReachableTiles = state.map.getReachableTiles(entities.teams[pk])

        def isTileSuitableFor(vyroba: Vyroba, tile: MapTile) -> bool:
            tileFeatures = set(tile.buildings).union(tile.entity.naturalResources)
            return all(f in tileFeatures for f in vyroba.requiredFeatures)

        def allowed_tiles(vyroba: Vyroba) -> List[EntityId]:
            return [t.id for t in teamReachableTiles if isTileSuitableFor(vyroba, t)]

        vList.sort(key=lambda x: x.id)
        return Response(
            {
                v.id: serializeEntity(v, {"allowedTiles": allowed_tiles(v)})
                for v in vList
            }
        )

    @action(detail=True)
    def buildings(self, request: Request, pk: TeamId) -> Response:
        self.validateAccess(request.user, pk)
        teamState, entities = self.getTeamStateAndEntities(pk)

        bList = list(teamState.buildings)
        bList.sort(key=lambda x: x.name)
        return Response({b.id: serializeEntity(b) for b in bList})

    @action(detail=True)
    def techs(self, request: Request, pk: TeamId) -> Response:
        self.validateAccess(request.user, pk)
        team = get_object_or_404(Team.objects.all(), pk=pk)

        state = self.getTeamState(pk)

        teamTechs = set()
        teamTechs.update(state.techs)
        teamTechs.update(state.researching)
        for t in state.techs:
            teamTechs.update([e for e in t.unlocks if isinstance(e, Tech)])

        def tech_extra_fields(tech):
            if tech in state.techs:
                return {"status": "owned"}
            if tech in state.researching:
                try:
                    assignment = DbTaskAssignment.objects.get(
                        team=team, techId=tech.id, finishedAt=None
                    )
                except DbTaskAssignment.DoesNotExist:
                    return {"status": "researching"}
                task = assignment.task
                return {
                    "status": "researching",
                    "assignedTask": {
                        "id": task.id,
                        "name": task.name,
                        "teamDescription": task.teamDescription,
                        "orgDescription": task.orgDescription,
                        "capacity": task.capacity,
                        "occupiedCount": task.occupiedCount,
                    },
                }
            return {"status": "available"}

        return Response(
            {
                tech.id: serializeEntity(tech, tech_extra_fields(tech))
                for tech in teamTechs
            }
        )

    @action(detail=True)
    def tasks(self, request: Request, pk: TeamId) -> Response:
        self.validateAccess(request.user, pk)
        team = get_object_or_404(Team.objects.all(), pk=pk)
        if request.user.isOrg:
            taskSet = DbTask.objects.all()
            serializer = DbTaskSerializer
        else:
            taskSet = DbTask.objects.filter(assignments__team=team.pk)
            serializer = PlayerDbTaskSerializer

        return Response({t.id: serializer(t).data for t in taskSet})

    @action(detail=True)
    def work(self, request: Request, pk: TeamId) -> Response:
        self.validateAccess(request.user, pk)
        state = self.getTeamState(pk)

        return Response({"work": state.work})

    @action(detail=True, methods=["POST"])
    def changetask(self, request: Request, pk: TeamId) -> Response:
        self.validateAccess(request.user, pk)
        team = get_object_or_404(Team.objects.all(), pk=pk)

        deserializer = ChangeTaskSerializer(data=request.data)
        deserializer.is_valid(raise_exception=True)
        data = deserializer.validated_data
        assert isinstance(data, dict)

        try:
            assignment = DbTaskAssignment.objects.get(
                team=team, techId=data["tech"], finishedAt=None
            )
            assignment.finishedAt = timezone.now()
            assignment.abandoned = True
            assignment.save()
        except DbTaskAssignment.DoesNotExist:
            pass

        if data["newTask"]:
            DbTaskAssignment.objects.create(
                team=team,
                task=get_object_or_404(DbTask.objects.all(), pk=data["newTask"]),
                techId=data["tech"],
            )
        return Response({})

    @action(detail=True)
    def dashboard(self, request: Request, pk: TeamId) -> Response:
        self.validateAccess(request.user, pk)
        team = get_object_or_404(Team.objects.all(), pk=pk)

        dbState = DbState.objects.latest("id")
        state = dbState.toIr()
        entities = dbState.entities
        teamState = state.teamStates[entities[pk]]

        feedRequirements = computeFeedRequirements(state, entities, entities[pk])

        return Response(
            {
                "population": {
                    "nospec": teamState.resources[entities["res-obyvatel"]],
                    "all": teamState.population,
                },
                "work": teamState.work,
                "culture": teamState.culture,
                "worldTurn": state.world.turn,
                "teamTurn": teamState.turn,
                "researchingTechs": [serializeEntity(x) for x in teamState.researching],
                "productions": [
                    (r.id, a)
                    for r, a in teamState.resources.items()
                    if r.isProduction and r.id != "res-obyvatel"
                ],
                "storage": [(r.id, a) for r, a in teamState.storage.items()],
                "granary": [
                    (r.id, a)
                    for r, a in teamState.granary.items()
                    if r.typ[0].id == "typ-jidlo"
                ]
                + [
                    (r.id, a)
                    for r, a in teamState.granary.items()
                    if r.typ[0].id == "typ-luxus"
                ],
                "feeding": {
                    "casteCount": feedRequirements.casteCount,
                    "tokensPerCaste": feedRequirements.tokensPerCaste,
                    "tokensRequired": feedRequirements.tokensRequired,
                },
                "announcements": [
                    {
                        "id": announcement.id,
                        "type": announcement.typeString(),
                        "content": announcement.content,
                        "read": False,
                        "appearDatetime": announcement.appearDatetime,
                    }
                    for announcement in self.unreadAnnouncements(request.user, team)
                ],
                "armies": [
                    self.serializeArmy(army, None)
                    for army in state.map.getTeamArmies(entities[pk])
                ],
                "techs": list(x.id for x in teamState.techs),
            }
        )

    @action(detail=True)
    def announcements(self, request: Request, pk: TeamId) -> Response:
        self.validateAccess(request.user, pk)
        team = get_object_or_404(Team.objects.all(), pk=pk)
        return Response(
            [
                {
                    "id": announcement.id,
                    "type": announcement.typeString(),
                    "content": announcement.content,
                    "read": request.user in announcement.read.all(),
                    "appearDatetime": announcement.appearDatetime,
                    "readBy": set([x.team.name for x in announcement.read.all()])
                    if request.user.isOrg
                    else None,
                }
                for announcement in Announcement.objects.getTeam(team)
            ]
        )

    @action(detail=True)
    def armies(self, request: Request, pk: TeamId) -> Response:
        self.validateAccess(request.user, pk)
        tState, entities = self.getTeamStateAndEntities(pk)
        state = tState.parent
        team = entities.teams[pk]
        reachableTiles = state.map.getReachableTiles(team)

        return Response(
            {
                a.index: self.serializeArmy(a, reachableTiles)
                for a in state.map.getTeamArmies(team)
            }
        )

    @action(detail=True)
    def stickers(self, request: Request, pk: TeamId) -> Response:
        self.validateAccess(request.user, pk)
        stickers = DbSticker.objects.filter(team__id=pk).order_by("-awardedAt")
        return Response(DbStickerSerializer(stickers, many=True).data)

    @action(detail=True)
    def storage(self, request: Request, pk: TeamId) -> Response:
        self.validateAccess(request.user, pk)
        storage = self.getTeamState(pk).storage

        assert all(amount >= 0 for amount in storage.values())
        return Response(
            {res.id: amount for res, amount in storage.items() if amount > 0}
        )

    @action(detail=True)
    def feeding(self, request: Request, pk: TeamId) -> Response:
        self.validateAccess(request.user, pk)
        teamState, entities = self.getTeamStateAndEntities(pk)
        state = teamState.parent

        return Response(
            stateSerialize(computeFeedRequirements(state, entities, entities.teams[pk]))
        )

    @action(detail=True)
    def tiles(self, request: Request, pk: TeamId) -> Response:
        self.validateAccess(request.user, pk)
        tState, entities = self.getTeamStateAndEntities(pk)
        state = tState.parent
        teamE = entities.teams[pk]
        reachableTiles = state.map.getReachableTiles(teamE)

        return Response(
            {
                tile.entity.id: {
                    "entity": serializeEntity(tile.entity),
                    "buildings": [x.id for x in tile.buildings],
                    "richness": tile.richness,
                }
                for tile in reachableTiles
            }
        )
