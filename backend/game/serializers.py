from rest_framework import serializers
from .models import DbTask

class DbTaskSerializer(serializers.ModelSerializer):
    techs = serializers.SlugRelatedField(slug_field="techId", many=True, read_only=True)
    class Meta:
        model = DbTask
        fields = "__all__"
