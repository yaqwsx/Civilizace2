from core.models.announcement import Announcement
from core.serializers import AnnouncementSerializer
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework import filters

class AnnouncementViewSet(viewsets.ModelViewSet):
    serializer_class = AnnouncementSerializer
    queryset = Announcement.objects.all()
    permission_classes = (IsAuthenticated,)
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ["appearDatetime"]
    ordering = ["-appearDatetime"]
