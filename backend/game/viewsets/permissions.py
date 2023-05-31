from typing import Any

from django.views import View
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request


class IsOrg(IsAuthenticated):
    def has_permission(self, request: Request, view: View) -> bool:
        return (
            super().has_permission(request, view)
            and request.user
            and request.user.is_org
        )


class IsSuperOrg(IsAuthenticated):
    def has_permission(self, request: Request, view: Any) -> bool:
        return (
            super().has_permission(request, view)
            and request.user
            and request.user.is_org
            and request.user.is_superuser
        )
