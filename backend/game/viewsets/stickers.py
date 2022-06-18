import io
from django.shortcuts import get_object_or_404
from django.utils import timezone
import requests
from game.models import DbEntities, DbSticker, Printer
from ipware import get_client_ip
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import APIException, PermissionDenied
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.http import FileResponse

from game.stickers import getStickerFile

class NoSuchPrinter(APIException):
    status_code = 400
    default_detail = "Taková tiskárna neexistuje"
    default_code = "bad_request"

class PrinterError(APIException):
    status_code = 400
    default_detail = "Tiskárna vrátila neočekávanou odpověď"
    default_code = "unexpected_response"

class DbStickerSerializer(serializers.ModelSerializer):
    class Meta:
        model = DbSticker
        fields = "__all__"
        editable=False

class PrintSerializer(serializers.Serializer):
    printerId = serializers.IntegerField()

class StickerViewSet(viewsets.ViewSet):
    def _getSticker(self, user, pk):
        sticker = get_object_or_404(DbSticker.objects.all(), pk=pk)
        # if not user.isOrg and user.team != sticker.team:
        #     raise PermissionDenied("Nedovolený přístup")
        return sticker

    def retrieve(self, request, pk):
        sticker = self._getSticker(request.user, pk)
        return Response(DbStickerSerializer(sticker).data)

    @action(detail=True, methods=["POST"])
    def upgrade(self, request, pk):
        sticker = self._getSticker(request.user, pk)
        sticker.update()
        sticker.save()
        return Response({})

    @staticmethod
    def printGeneral(request, imageFileStream) -> Response:
        deserializer = PrintSerializer(data=request.data)
        deserializer.is_valid(raise_exception=True)
        data = deserializer.validated_data

        Printer.objects.prune()
        try:
            printer = Printer.objects.get(pk=data["printerId"])
        except Printer.DoesNotExist:
            raise NoSuchPrinter() from None

        try:
            printerUrl = f"http://{printer.address}:{printer.port}/print"
            r = requests.post(printerUrl, files={
                "image": imageFileStream
            })
            if r.status_code != 200:
                raise PrinterError(r.text)
        except Exception as e:
            raise PrinterError(str(e))
        return Response({})

    @action(detail=True, methods=["POST"])
    def print(self, request, pk):
        sticker = self._getSticker(request.user, pk)

        return self.printGeneral(request, open(getStickerFile(sticker), "rb"))

    # @action(detail=True, methods=["POST"])
    # def printRelated(self, request, pk):
    #     rootSticker = self._getSticker(request.user, pk)
    #     if not rootSticker.entityId.startswith("tec-"):
    #         return self.print(request, pk)
    #     revision, entities = DbEntities.objects.get_revision()

    #     relatedStickers =
    #     return self.printGeneral(request, open(getStickerFile(sticker), "rb"))

    @action(detail=True, methods=["GET"])
    def image(self, request, pk):
        sticker = self._getSticker(request.user, pk)
        return FileResponse(open(getStickerFile(sticker), "rb"), filename=f"sticker_{sticker.id}.png")

