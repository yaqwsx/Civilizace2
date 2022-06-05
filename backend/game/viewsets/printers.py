from game.models import Printer
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework import serializers
from django.utils import timezone

from ipware import get_client_ip

class NoIPError(APIException):
    status_code = 403
    default_detail = "Cannot get client IP address"
    default_code = "forbidden"

class PrinterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Printer
        fields = "__all__"
        read_only_fields = ["id", "address", "registeredAt"]

class PrinterViewSet(viewsets.ViewSet):
    def list(self, request):
        Printer.objects.prune()
        return Response(PrinterSerializer(Printer.objects.all(), many=True).data)

    @action(detail=False, methods=["POST"])
    def register(self, request):
        deserializer = PrinterSerializer(data=request.data)
        deserializer.is_valid(raise_exception=True)
        data = deserializer.validated_data

        clientIp, _ = get_client_ip(request)
        if clientIp is None:
            raise NoIPError()
        Printer.objects.update_or_create(name=data["name"], defaults={
            "address": clientIp,
            "port": data["port"],
            "registeredAt": timezone.now(),
            "printsStickers": data["printsStickers"]
        })
        return Response()

