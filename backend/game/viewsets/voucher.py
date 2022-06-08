import io
from django.shortcuts import get_object_or_404
from django.db import transaction
from rest_framework import serializers, viewsets, mixins
from rest_framework.decorators import action
from rest_framework.exceptions import APIException
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from game.models import DbDelayedEffect, DbEntities, DbState
from game.stickers import makeVoucherSticker
from game.viewsets.action import ActionViewSet
from game.viewsets.stickers import StickerViewSet
from game.viewsets.permissions import IsOrg


class DbDelayedEffectSerializer(serializers.ModelSerializer):
    description = serializers.CharField()
    class Meta:
        model = DbDelayedEffect
        fields = ["slug", "description", "round", "target", "performed", "stickers", "withdrawn", "team"]

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
        for e in DbDelayedEffect.objects.filter(withdrawn=False, slug__in=slugs):
            r, gainedStickers = ActionViewSet.awardDelayedEffect(e)
            ActionViewSet.addResultNotifications(r)
            stickers.update(e.stickers)
            messages.append(f"## {e.description} ({e.slug})\n\n{r.message}")
        if len(messages) == 0:
            messages.append("Nebyly provedeny žádné výběry")
        return Response({
            "stickers": list(stickers),
            "messages": "\n\n".join(messages) # Put slugs in between as headings
        })

    @action(detail=True, methods=["POST"])
    def print(self, request, pk):
        effect = get_object_or_404(DbDelayedEffect.objects.all(), slug=pk)
        img = makeVoucherSticker(effect)

        imgStream = io.BytesIO()
        img.save(imgStream, format="PNG")
        imgStream.seek(0)

        return StickerViewSet.printGeneral(request, imgStream)
