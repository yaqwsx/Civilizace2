from game.models import DbMapDiff
from game.viewsets.permissions import IsOrg
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework import serializers


class DbMapDiffSerializer(serializers.ModelSerializer):
    class Meta:
        model = DbMapDiff
        fields = "__all__"


class MapDiffViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated, IsOrg)

    queryset = DbMapDiff.objects.all().order_by("createdAt")
    serializer_class = DbMapDiffSerializer
