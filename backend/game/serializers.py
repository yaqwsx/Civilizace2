from rest_framework import serializers
from .models import DbTask, DbTaskPreference

from core.serializers.fields import IdRelatedField

class DbTaskSerializer(serializers.ModelSerializer):
    techs = IdRelatedField(slug_field="techId",
            many=True,
            read_only=False,
            queryset=DbTaskPreference.objects.all())
    class Meta:
        model = DbTask
        fields = "__all__"
        read_only_fields = ["id"]

    @staticmethod
    def _withoutTechs(data):
        return {k: v for k, v in data.items() if k != "techs"}

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
