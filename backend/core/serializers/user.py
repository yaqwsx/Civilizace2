from core.models import User
from rest_framework import serializers

from core.serializers.team import TeamSerializer


class UserSerializer(serializers.ModelSerializer):
    team = TeamSerializer()

    class Meta:
        model = User
        fields = ["id", "username", "is_org", "team", "is_superuser"]
        read_only_field = []
