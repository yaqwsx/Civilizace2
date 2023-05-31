from rest_framework import serializers

from core.models import Team


class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ["id", "name", "color"]
        read_only_field = []
