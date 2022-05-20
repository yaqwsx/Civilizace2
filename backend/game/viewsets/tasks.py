from game.models import DbTask
from ..serializers import DbTaskSerializer
from rest_framework import viewsets

class TaskViewSet(viewsets.ModelViewSet):
    queryset = DbTask.objects.all()
    serializer_class = DbTaskSerializer

