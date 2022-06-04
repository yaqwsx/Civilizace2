from django.shortcuts import get_object_or_404
from django.db import transaction
from rest_framework import serializers, viewsets, mixins
from rest_framework.decorators import action
from rest_framework.exceptions import APIException
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from game.models import DbDelayedEffect, DbEntities, DbState
from game.viewsets.action import ActionViewSet
from game.viewsets.permissions import IsOrg


class DbDelayedEffectSerializer(serializers.ModelSerializer):
    class Meta:
        model = DbDelayedEffect
        fields = ["slug", "round", "target", "result", "stickers", "withdrawn"]

class VoucherViewSet(viewsets.ViewSet):
    permission_classes = (IsAuthenticated, IsOrg)

    def retrieve(self, request, pk):
        t = get_object_or_404(DbDelayedEffect.objects.all(), slug=pk)
        serializer = DbDelayedEffectSerializer(t)
        return Response(serializer.data)

    @action(detail=False, methods=["POST"])
    @transaction.atomic
    def withdraw(self, request):
        slugs = request.data.get("keys", [])
        stickers = set()
        messages = []
        materials = {}
        for e in DbDelayedEffect.objects.filter(withdrawn=False, slug__in=slugs):
            r, s = ActionViewSet.awardDelayedEffect(e)
            e.withdraw = True
            e.save()
            stickers.update(s)
            messages.append(r.message)
            for m, a in r.materials.items():
                materials[m] = materials.get(m, 0) + a
        return Response({
            "stickers": list(stickers),
            "materials": {m.id: a for m, a in materials.items()},
            "messages": "\n\n".join(messages) # Put slugs in between as headings
        })
