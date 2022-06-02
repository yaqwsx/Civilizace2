from game.models import DbTask, DbTaskAssignment, DbTurn
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework import serializers
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from django.utils import timezone



class TurnImmutableError(APIException):
    status_code = 403
    default_detail = "Kolo již nelze editovat"
    default_code = "forbidden"

class DbTurnSerializer(serializers.ModelSerializer):
    class Meta:
        model=DbTurn
        fields = "__all__"
        read_only_fields = ["id", "startedAt"]

class TurnsViewSet(viewsets.ViewSet):
    permission_classes = (IsAuthenticated,)

    def list(self, request):
        if not request.user.isOrg:
            raise PermissionError()
        turns = DbTurn.objects.all()
        serializer = DbTurnSerializer(turns, many=True)
        return Response(serializer.data)

    def update(self, request, pk):
        if not request.user.isOrg:
            raise PermissionError()

        turn = get_object_or_404(DbTurn, pk=pk)

        deserializer = DbTurnSerializer(data=request.data)
        deserializer.is_valid(raise_exception=True)
        data = deserializer.validated_data

        if turn.startedAt is not None:
            raise TurnImmutableError()

        turn.enabled = data["enabled"]
        turn.duration = data["duration"]
        turn.save()

        return Response(DbTurnSerializer(turn).data)

    @action(detail=False)
    def active(self, request):
        try:
            turn = DbTurn.objects.getActiveTurn()
            remaining = turn.startedAt + timezone.timedelta(seconds=turn.duration) - timezone.now()
            secsRemaining = remaining.total_seconds()
            if secsRemaining < 0:
                return Response({"id": -1})
            return Response(DbTurnSerializer(turn).data)
        except DbTurn.DoesNotExist:
            return Response({"id": -1})
