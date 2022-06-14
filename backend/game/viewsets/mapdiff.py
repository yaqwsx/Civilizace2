from game.models import DbMapDiff, DbTask, DbTaskAssignment
from game.viewsets.permissions import IsOrg
from ..serializers import DbTaskSerializer
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework import serializers

from rest_framework.exceptions import APIException


class DbMapDiffSerializer(serializers.ModelSerializer):
    class Meta:
        model = DbMapDiff
        fields = "__all__"

class MapDiffViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated, IsOrg)

    queryset = DbMapDiff.objects.all().order_by("createdAt")
    serializer_class = DbMapDiffSerializer

