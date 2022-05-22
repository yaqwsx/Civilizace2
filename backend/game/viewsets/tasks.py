from game.models import DbTask
from game.viewsets.permissions import IsOrg
from ..serializers import DbTaskSerializer
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

class TaskViewSet(viewsets.ModelViewSet):
    # permission_classes = (IsAuthenticated, IsOrg)

    queryset = DbTask.objects.all()
    serializer_class = DbTaskSerializer

