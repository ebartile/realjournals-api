from django.utils.translation import gettext_lazy as _
from rest_framework import permissions
from . import services
from apps.utils.exceptions import PermissionDenied
from django.apps import apps
import abc

class PermissionComponent(object, metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def has_object_permission(self, request, view, obj=None):
        pass

    def has_permission(self, request, view):
        return True

    def __invert__(self):
        return Not(self)

    def __and__(self, component):
        return And(self, component)

    def __or__(self, component):
        return Or(self, component)

class PermissionOperator(PermissionComponent):
    """
    Base class for all logical operators for compose
    components.
    """

    def __init__(self, *components):
        self.components = tuple(components)

class Not(PermissionOperator):
    """
    Negation operator as permission composable component.
    """

    # Overwrites the default constructor for fix
    # to one parameter instead of variable list of them.
    def __init__(self, component):
        super().__init__(component)

    def has_object_permission(self, *args, **kwargs):
        component = self.components[0]
        return (not component.has_object_permission(*args, **kwargs))


class Or(PermissionOperator):
    """
    Or logical operator as permission component.
    """

    def has_object_permission(self, *args, **kwargs):
        valid = False

        for component in self.components:
            if component.has_object_permission(*args, **kwargs):
                valid = True
                break

        return valid


class And(PermissionOperator):
    """
    And logical operator as permission component.
    """

    def has_object_permission(self, *args, **kwargs):
        valid = True

        for component in self.components:
            if not component.has_object_permission(*args, **kwargs):
                valid = False
                break

        return valid

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


 