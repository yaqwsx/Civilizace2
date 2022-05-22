from game.models import DbTask, DbTaskAssignment
from game.viewsets.permissions import IsOrg
from ..serializers import DbTaskSerializer
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from rest_framework.exceptions import APIException

class TaskUsedError(APIException):
    status_code = 403
    default_detail = "Úkol byl již přiřazen nějakému týmu. Takový úkol nelze smazat"
    default_code = "forbidden"

class TaskViewSet(viewsets.ModelViewSet):
    # permission_classes = (IsAuthenticated, IsOrg)

    queryset = DbTask.objects.all()
    serializer_class = DbTaskSerializer

    def destroy(self, request, pk, *args, **kwargs):
        t = DbTask.objects.get(pk=pk)
        if DbTaskAssignment.objects.filter(task=t).exists():
            raise TaskUsedError()
        return super().destroy(request, pk, *args, **kwargs)

