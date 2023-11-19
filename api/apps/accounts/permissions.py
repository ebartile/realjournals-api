from django.utils.translation import gettext_lazy as _
from rest_framework import permissions
from . import services
from apps.utils.exceptions import PermissionDenied
from django.apps import apps
from apps.history.permissions import PermissionComponent

class HasAccountPerm(PermissionComponent):
    def __init__(self, perm, *components):
        self.account_perm = perm
        super().__init__(*components)

    def has_permission(self, request, view):
        return True

    def has_object_permission(self, request, view, obj=None):
        return services.user_has_perm(request.user, self.account_perm, obj)

class IsObjectOwner(permissions.BasePermission):

    def has_permission(self, request, view):
        return True

    def has_object_permission(self, request, view, obj):
        if obj.owner is None:
            return False

        return obj.owner == request.user

class IsAccountAdmin(permissions.BasePermission):

    def has_permission(self, request, view):
        return True

    def has_object_permission(self, request, view, obj):
        return services.is_account_admin(request.user, obj)

class CanLeaveAccount(permissions.BasePermission):
    
    def has_permission(self, request, view):
        return True

    def has_object_permission(self, request, view, obj):
        if not obj or not request.user.is_authenticated:
            return False

        Membership = apps.get_model('accounts', 'Membership')

        try:
            if not services.can_user_leave_account(request.user, obj):
                raise PermissionDenied(_("You can't leave the account if you are the owner or there are "
                                             "no more admins"))
            return True
        except Membership.DoesNotExist:
            return False


 