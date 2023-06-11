from __future__ import annotations

from decimal import Decimal
from typing import Any, Iterable, NamedTuple, Optional, TypedDict, Union

from django.db import transaction
from django.db.models.query import QuerySet
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from core.models import Team, User
from core.models.announcement import Announcement
from core.serializers.team import TeamSerializer
from game.actions.feed import computeFeedRequirements
from game.entities import Entities, EntityId, TeamEntity, Vyroba
from game.gameGlue import serializeEntity, stateSerialize
from game.models import DbState, DbSticker, DbTask, DbTaskAssignment, DbTaskManager
from game.serializers import DbTaskSerializer, PlayerDbTaskSerializer
from game.state import Army, GameState, MapTile, TeamState
from game.viewsets.permissions import IsOrg
from game.viewsets.stickers import DbStickerSerializer

TeamId = str  # intentionally left weak


class ChangeTaskSerializer(serializers.Serializer):
    tech = serializers.CharField()
    newTask = serializers.CharField(allow_blank=True, allow_null=True)


class SpecialResources(TypedDict):
    work: Decimal
    obyvatels: Decimal
    population: Decimal
    culture: Decimal
    withdraw_capacity: Decimal


class TeamStateInfo(NamedTuple):
    state: GameState
    teamEntity: TeamEntity
    entities: Entities

    @property
    def teamState(self) -> TeamState:
        return self.state.teamStates[self.teamEntity]

    def getTeamSpecialResources(self) -> SpecialResources:
        resources = self.teamState.resources
        return {
            "work": resources.get(self.entities.work, Decimal(0)),
            "obyvatels": resources.get(self.entities.obyvatel, Decimal(0)),
            "population": self.teamState.population,
            "culture": resources.get(self.entities.culture, Decimal(0)),
            "withdraw_capacity": resources.get(
                self.entities.withdraw_capacity, Decimal(0)
            ),
        }

    @staticmethod
    def get_latest(teamId: TeamId) -> TeamStateInfo:
        dbState = DbState.get_latest()
        state = dbState.toIr()
        entities = dbState.entities
        return TeamStateInfo(state, entities.teams[teamId], entities)


class TeamViewSet(viewsets.ViewSet):
    permission_classes = (IsAuthenticated,)

    def validateAccess(self, user: User, teamId: TeamId) -> None:
        if not user.is_org:
            assert user.team is not None
            if user.team.id != teamId:
                raise PermissionDenied("Nedovolený přístup")

    def unreadAnnouncements(self, user: User, team: Team) -> QuerySet[Announcement]:
        if user.is_org:
            return Announcement.objects.get_team_unread(team)
        return Announcement.objects.get_unread(user)

    def retrieve(self, request: Request, pk: TeamId) -> Response:
        self.validateAccess(request.user, pk)

        t = get_object_or_404(Team.objects.filter(visible=True), pk=pk)
        return Response(TeamSerializer(t).data)

    @staticmethod
    def serializeArmy(
        a: Army, reachableTiles: Optional[Iterable[MapTile]]
    ) -> dict[str, Any]:
        return {
            "index": a.index,
            "team": a.team.id,
            "name": a.name,
            "level": a.level,
            "equipment": a.equipment,
            "boost": a.boost,
            "tile": a.tile.id if a.tile is not None else None,
            "mode": a.mode.name,
            "goal": a.goal.name if a.goal is not None else None,
            "reachableTiles": [t.id for t in reachableTiles]
            if reachableTiles is not None
            else None,
        }

    @action(detail=True)
    def resources(self, request: Request, pk: TeamId) -> Response:
        self.validateAccess(request.user, pk)
        resources = TeamStateInfo.get_latest(pk).teamState.resources

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
        stateInfo = TeamStateInfo.get_latest(pk)

        teamReachableTiles = stateInfo.state.map.getReachableTiles(stateInfo.teamEntity)

        def isTileSuitableFor(vyroba: Vyroba, tile: MapTile) -> bool:
            return set(vyroba.requiredTileFeatures).issubset(tile.features)

        def allowed_tiles(vyroba: Vyroba) -> list[EntityId]:
            return [t.id for t in teamReachableTiles if isTileSuitableFor(vyroba, t)]

        return Response(
            {
                v.id: serializeEntity(v, {"allowedTiles": allowed_tiles(v)})
                for v in stateInfo.teamState.unlocked_vyrobas()
            }
        )

    @action(detail=True)
    def buildings(self, request: Request, pk: TeamId) -> Response:
        self.validateAccess(request.user, pk)
        teamState = TeamStateInfo.get_latest(pk).teamState
        return Response(
            {b.id: serializeEntity(b) for b in teamState.unlocked_buildings()}
        )

    @action(detail=True)
    def building_upgrades(self, request: Request, pk: TeamId) -> Response:
        self.validateAccess(request.user, pk)
        teamState = TeamStateInfo.get_latest(pk).teamState
        return Response(
            {u.id: serializeEntity(u) for u in teamState.unlocked_building_upgrades()}
        )

    @action(detail=True)
    def attributes(self, request: Request, pk: TeamId) -> Response:
        self.validateAccess(request.user, pk)
        teamState = TeamStateInfo.get_latest(pk).teamState

        return Response(
            {
                a.id: serializeEntity(a, {"owned": a in teamState.attributes})
                for a in teamState.unlocked_attributes()
            }
        )

    @staticmethod
    def serialize_task(task: Union[DbTask, DbTaskManager], user: User):
        if user.is_org:
            return DbTaskSerializer(task).data
        else:
            return PlayerDbTaskSerializer(task).data

    @action(detail=True)
    def techs(self, request: Request, pk: TeamId) -> Response:
        self.validateAccess(request.user, pk)
        team = get_object_or_404(Team.objects.all(), pk=pk)

        teamState = TeamStateInfo.get_latest(pk).teamState

        teamTechs = set(teamState.techs)
        teamTechs.update(teamState.researching)
        for t in teamState.techs:
            teamTechs.update(t.unlocksTechs)

        def tech_extra_fields(tech):
            if tech in teamState.techs:
                return {"status": "owned"}
            if tech in teamState.researching:
                try:
                    assignment = DbTaskAssignment.objects.get(
                        team=team, techId=tech.id, finishedAt=None
                    )
                except DbTaskAssignment.DoesNotExist:
                    return {"status": "researching"}
                return {
                    "status": "researching",
                    "assignedTask": TeamViewSet.serialize_task(
                        assignment.task, request.user
                    ),
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
        if request.user.is_org:
            taskSet = DbTask.objects.all()
        else:
            taskSet = DbTask.objects.filter(assignments__team=pk)

        return Response(
            {t.id: TeamViewSet.serialize_task(t, request.user) for t in taskSet}
        )

    @action(detail=True)
    def special_resources(self, request: Request, pk: TeamId) -> Response:
        self.validateAccess(request.user, pk)
        stateInfo = TeamStateInfo.get_latest(pk)
        return Response(stateInfo.getTeamSpecialResources())

    @action(detail=True, methods=["POST"], permission_classes=[IsOrg])
    @transaction.atomic()
    def changetask(self, request: Request, pk: TeamId) -> Response:
        assert request.user.is_org
        team = get_object_or_404(Team.objects.all(), pk=pk)

        deserializer = ChangeTaskSerializer(data=request.data)
        deserializer.is_valid(raise_exception=True)
        data = deserializer.validated_data
        assert isinstance(data, dict)

        if newTaskPk := data["newTask"]:
            newTask = get_object_or_404(DbTask.objects.all(), pk=newTaskPk)
        else:
            newTask = None

        try:
            assignment = DbTaskAssignment.objects.get(
                team=team, techId=data["tech"], finishedAt=None
            )
            assignment.finishedAt = timezone.now()
            assignment.abandoned = True
            assignment.save()
        except DbTaskAssignment.DoesNotExist:
            pass

        if newTask is not None:
            DbTaskAssignment.objects.create(
                team=team,
                task=newTask,
                techId=data["tech"],
            )
        return Response({})

    @action(detail=True)
    def dashboard(self, request: Request, pk: TeamId) -> Response:
        self.validateAccess(request.user, pk)
        team = get_object_or_404(Team.objects.all(), pk=pk)
        stateInfo = TeamStateInfo.get_latest(pk)
        teamState = stateInfo.teamState
        entities = stateInfo.entities

        orgInfo = {
            "groups": list(x.id for x in stateInfo.teamEntity.groups),
            "techs": list(x.id for x in teamState.techs),
            "attributes": list(x.id for x in teamState.attributes),
        }

        return Response(
            {
                "specialres": stateInfo.getTeamSpecialResources(),
                "worldTurn": stateInfo.state.world.turn,
                "teamTurn": teamState.turn,
                "researching": [serializeEntity(x) for x in teamState.researching],
                "productions": [(r.id, a) for r, a in teamState.productions.items()],
                "storage": [(r.id, a) for r, a in teamState.storage.items()],
                "granary": [(r.id, a) for r, a in teamState.granary.items()],
                "feeding": stateSerialize(
                    computeFeedRequirements(
                        stateInfo.state, entities, stateInfo.teamEntity
                    )
                ),
                "announcements": [
                    {
                        "id": announcement.id,
                        "type": announcement.type.name,
                        "content": announcement.content,
                        "read": False,
                        "appearDatetime": announcement.appearDatetime,
                    }
                    for announcement in self.unreadAnnouncements(request.user, team)
                ],
                "armies": [
                    self.serializeArmy(army, None)
                    for army in stateInfo.state.map.getTeamArmies(stateInfo.teamEntity)
                ],
                **({"orginfo": orgInfo} if request.user.is_org else {}),
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
                    "type": announcement.type.name,
                    "content": announcement.content,
                    "read": request.user in announcement.read.all(),
                    "appearDatetime": announcement.appearDatetime,
                    "readBy": set([x.team.name for x in announcement.read.all()])
                    if request.user.is_org
                    else None,
                }
                for announcement in Announcement.objects.get_team(team)
            ]
        )

    @action(detail=True)
    def armies(self, request: Request, pk: TeamId) -> Response:
        self.validateAccess(request.user, pk)
        stateInfo = TeamStateInfo.get_latest(pk)
        reachableTiles = stateInfo.state.map.getReachableTiles(stateInfo.teamEntity)

        return Response(
            {
                a.index: self.serializeArmy(a, reachableTiles)
                for a in stateInfo.state.map.getTeamArmies(stateInfo.teamEntity)
            }
        )

    @action(detail=True)
    def stickers(self, request: Request, pk: TeamId) -> Response:
        self.validateAccess(request.user, pk)
        stickers = DbSticker.objects.filter(team=pk).order_by("-awardedAt")
        return Response(DbStickerSerializer(stickers, many=True).data)

    @action(detail=True)
    def storage(self, request: Request, pk: TeamId) -> Response:
        self.validateAccess(request.user, pk)
        teamState = TeamStateInfo.get_latest(pk).teamState
        storage = teamState.storage
        assert all(amount >= 0 for amount in storage.values())
        return Response(
            {res.id: amount for res, amount in storage.items() if amount > 0}
        )

    @action(detail=True)
    def feeding(self, request: Request, pk: TeamId) -> Response:
        self.validateAccess(request.user, pk)
        stateInfo = TeamStateInfo.get_latest(pk)

        return Response(
            stateSerialize(
                computeFeedRequirements(
                    stateInfo.state, stateInfo.entities, stateInfo.teamEntity
                )
            )
        )

    @action(detail=True)
    def tiles(self, request: Request, pk: TeamId) -> Response:
        self.validateAccess(request.user, pk)
        stateInfo = TeamStateInfo.get_latest(pk)
        reachableTiles = stateInfo.state.map.getReachableTiles(stateInfo.teamEntity)

        return Response(
            {
                tile.entity.id: serializeEntity(
                    tile.entity,
                    {
                        "is_home": tile.entity == stateInfo.teamEntity.homeTile,
                        "buildings": [x.id for x in tile.buildings],
                        "building_upgrades": [x.id for x in tile.building_upgrades],
                    },
                )
                for tile in reachableTiles
            }
        )
