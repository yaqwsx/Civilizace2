from django.shortcuts import get_object_or_404
from core.serializers import TeamSerializer
from core.models import Team, User
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework import filters


class TeamViewSet(viewsets.ModelViewSet):
    http_method_names = ["get"]
    serializer_class = TeamSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ["id"]
    ordering = ["-id"]

    def get_queryset(self):
        assert isinstance(self.request.user, User)
        if self.request.user.isOrg:
            return Team.objects.all()
        return Team.objects.filter(visible=True)

    def get_object(self):
        lookupFieldValue = self.kwargs[self.lookup_field]

        obj = get_object_or_404(self.get_queryset(), pk=lookupFieldValue)
        self.check_object_permissions(self.request, obj)

        return obj
