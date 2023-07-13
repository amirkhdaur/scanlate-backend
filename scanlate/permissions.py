from rest_framework.permissions import BasePermission

from .models import Title, Chapter


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user.is_authenticated and request.user.is_admin)


class IsUser(BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user == obj


def has_role(request, obj, slug):
    if isinstance(obj, Title):
        title = obj
    elif isinstance(obj, Chapter):
        title = obj.title
    else:
        return False

    return bool(title.workers.filter(user=request.user, role__slug=slug).exists())


class IsRawProvider(BasePermission):
    def has_permission(self, request, view):
        view.get_queryset()

    def has_object_permission(self, request, view, obj):
        return has_role(request, obj, 'raw-provider')


class IsCurator(BasePermission):
    def has_object_permission(self, request, view, obj):
        return has_role(request, obj, 'curator')


class IsQualityChecker(BasePermission):
    def has_object_permission(self, request, view, obj):
        return has_role(request, obj, 'quality-checker')
