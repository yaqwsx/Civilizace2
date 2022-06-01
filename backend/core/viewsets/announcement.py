from core.models.announcement import Announcement
from core.serializers import AnnouncementSerializer
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework import filters
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404

class AnnouncementViewSet(viewsets.ModelViewSet):
    serializer_class = AnnouncementSerializer
    queryset = Announcement.objects.all()
    permission_classes = (IsAuthenticated,)
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ["appearDatetime"]
    ordering = ["-appearDatetime"]


    @action(detail=True, methods=["POST"])
    def read(self, request, pk):
        announcement = get_object_or_404(Announcement, pk=pk)
        announcement.read.add(request.user)
        announcement.save()
        return Response({})

