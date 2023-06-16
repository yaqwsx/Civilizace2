from rest_framework import serializers, viewsets
from rest_framework.permissions import IsAuthenticated

from core.serializers.fields import TextEnumSerializer
from game.models import DbMapDiff, DiffType
from game.viewsets.permissions import IsOrg


class DbMapDiffSerializer(serializers.ModelSerializer):
    type = TextEnumSerializer(DiffType)

    class Meta:
        model = DbMapDiff
        fields = "__all__"


class MapDiffViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated, IsOrg)

    queryset = DbMapDiff.objects.all().order_by("createdAt")
    serializer_class = DbMapDiffSerializer
