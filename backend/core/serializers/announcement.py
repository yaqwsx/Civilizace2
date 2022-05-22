from django.shortcuts import get_object_or_404
from rest_framework import serializers
from core.models.announcement import Announcement, AnnouncementType
from core.models.team import Team
from core.models.user import User
from core.serializers.fields import IdRelatedField, TextEnumField
from core.serializers.user import UserSerializer
from django.contrib.auth.models import AnonymousUser

class TeamIdSerializer(serializers.ModelSerializer):
    class Meta(object):
        model = Team
        fields = ("id",)

    def to_representation(self, value):
        return value.id

    def to_internal_value(self, data):
        return get_object_or_404(Team, pk=data)

class AnnouncementSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    teams = TeamIdSerializer(many=True)
    type = TextEnumField(AnnouncementType.choices)

    class Meta:
        model = Announcement
        fields = "__all__"
        read_only_fields = ["id", "read", "author"]


    @staticmethod
    def _withoutTeams(data):
        return {k: v for k, v in data.items() if k != "teams"}

    def _setAuthor(self, announcement):
        user = None
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            user = request.user
        if isinstance(user, User):
            announcement.author = user

    def create(self, validated_data):
        announcement = Announcement.objects.create(**self._withoutTeams(validated_data))
        for t in validated_data["teams"]:
            announcement.teams.add(t)
        self._setAuthor(announcement)
        announcement.save()
        return announcement

    def update(self, instance, validated_data):
        announcement = super().update(instance, self._withoutTeams(validated_data))
        announcement.teams.clear()
        for t in validated_data["teams"]:
            announcement.teams.add(t)
        self._setAuthor(announcement)
        announcement.save()
        return announcement
