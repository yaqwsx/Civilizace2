from rest_framework.permissions import BasePermission

class IsOrg(BasePermission):
    def has_permission(self, request, view):
        return request.user.isOrg()

class IsSuperOrg(BasePermission):
    def has_object_permission(self, request, view):
        return request.user.isOrg() and request.user.isSuperUser()
