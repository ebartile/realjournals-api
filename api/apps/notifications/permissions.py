
from rest_framework import permissions

class WebNotificationsPermission(permissions.BasePermission):

    def has_permission(self, request, view):
        return True

    def has_object_permission(self, request, view, obj):
        return obj and request.user.is_authenticated and \
               request.user.pk == obj.user_id