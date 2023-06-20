from django.shortcuts import get_object_or_404
from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from core.models.announcement import Announcement, AnnouncementType
from core.serializers import AnnouncementSerializer
from core.serializers.announcement import team_serialize_announcement


class AnnouncementViewSet(viewsets.ModelViewSet):
    serializer_class = AnnouncementSerializer
    queryset = Announcement.objects.exclude(type=AnnouncementType.game)
    permission_classes = (IsAuthenticated,)
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ["appearDatetime"]
    ordering = ["-appearDatetime"]

    @action(detail=True, methods=["POST"])
    def read(self, request: Request, pk) -> Response:
        announcement = get_object_or_404(Announcement, pk=pk)
        announcement.read.add(request.user)
        announcement.save()
        return Response({})

    @action(detail=False)
    def public(self, request: Request) -> Response:
        announcements = Announcement.objects.get_public()[:5]
        return Response(
            [
                team_serialize_announcement(
                    a, read=request.user in a.read.all(), org_info=request.user.is_org
                )
                for a in announcements
            ]
        )
