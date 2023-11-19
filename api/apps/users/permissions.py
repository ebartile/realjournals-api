from rest_framework import permissions
from django.utils.translation import gettext_lazy as _
from django.conf import settings

class CanRetrieveUser(permissions.BasePermission):

    def has_permission(self, request, view):
        return True

    def has_object_permission(self, request, view, obj):
        # TODO: you need to be a memberships
        if settings.PRIVATE_USER_PROFILES:
            return obj and request.user and request.user.is_authenticated

        return True

class IsTheSameUser(permissions.BasePermission):

    def has_permission(self, request, view):
        return True

    def has_object_permission(self, request, view, obj):
        return obj and request.user.is_authenticated and request.user.pk == obj.pk

