from rest_framework import serializers
from .models import DbTask, DbTaskPreference, DbTaskAssignment, DbAction, DbInteraction

from core.serializers.fields import IdRelatedField

class DbTaskAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = DbTaskAssignment
        fields = ["team", "techId", "assignedAt", "finishedAt"]

class DbTaskSerializer(serializers.ModelSerializer):
    techs = IdRelatedField(slug_field="techId",
            many=True,
            read_only=False,
            queryset=DbTaskPreference.objects.all())
    assignments = DbTaskAssignmentSerializer(many=True)
    occupiedCount = serializers.IntegerField()
    class Meta:
        model = DbTask
        fields = "__all__"
        read_only_fields = ["id", "assignments", "occupiedCount"]

    @staticmethod
    def _withoutTechs(data):
        # occupiedCount shouldn't be here, but, meh, whatever
        return {k: v for k, v in data.items() if k not in ["techs", "assignments", "occupiedCount"]}

    def create(self, validated_data):
        task = DbTask.objects.create(**self._withoutTechs(validated_data))
        for t in validated_data["techs"]:
            task.techs.add(DbTaskPreference(techId=t), bulk=False)
        return task

    def update(self, instance, validated_data):
        retval =  super().update(instance, self._withoutTechs(validated_data))
        DbTaskPreference.objects \
            .filter(task=retval) \
            .exclude(techId__in=validated_data["techs"]) \
            .delete()
        for tech in validated_data["techs"]:
            DbTaskPreference.objects.get_or_create(task=retval, techId=tech)
        return retval

class PlayerDbTaskSerializer(DbTaskSerializer):
    class Meta(DbTaskSerializer.Meta):
        fields = ["id", "name", "teamDescription", "assignments"]


class DbInteractionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DbInteraction
        fields = "__all__"

    author = serializers.SlugRelatedField(slug_field="username", read_only=True)


class DbActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DbAction
        fields = "__all__"

    interactions = DbInteractionSerializer(many=True, read_only=True)

