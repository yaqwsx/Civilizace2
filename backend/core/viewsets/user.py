from core.serializers import UserSerializer
from core.models import User
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, IsAdminUser


class UserViewSet(viewsets.ModelViewSet):
    http_method_names = ["get"]
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated, IsAdminUser)

    queryset = User.objects.all()
