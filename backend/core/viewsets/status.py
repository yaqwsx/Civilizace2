from rest_framework import viewsets
from rest_framework.request import Request
from rest_framework.response import Response


class StatusViewSet(viewsets.ViewSet):
    def list(self, request: Request):
        return Response({"status": "OK"})
