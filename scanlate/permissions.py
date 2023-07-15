from rest_framework import permissions

from .models import Role


class IsSafeMethod(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True


class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user.is_authenticated and request.user.is_admin)


class IsUser(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj == request.user


class IsCurator(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and (Role.CURATOR in request.user.roles)
