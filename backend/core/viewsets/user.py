from core.serializers import UserSerializer
from core.models import User
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework import filters


class UserViewSet(viewsets.ModelViewSet):
    http_method_names = ["get"]
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ["updated"]
    ordering = ["-updated"]

    def get_queryset(self):
        if self.requests.user.is_superuser:
            return User.objects.all()
        return User.objects.filter(pk=self.requests.user.pk)

    def get_object(self):
        lookupFieldValue = self.kwargs[self.lookup_field]

        obj = User.objects.get(pk=lookupFieldValue)
        self.check_object_permissions(self.request, obj)

        return obj
