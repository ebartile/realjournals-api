import abc
from .services import get_model_from_key, get_pk_from_key
from apps.accounts.services import is_account_admin

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

class IsCommentOwner(PermissionComponent):

    def has_object_permission(self, request, view, obj=None):
        return obj.user and obj.user.get("pk", "not-pk") == request.user.pk

class IsCommentAccountAdmin(PermissionComponent):

    def has_object_permission(self, request, view, obj=None):
        model = get_model_from_key(obj.key)
        pk = get_pk_from_key(obj.key)
        account = model.objects.get(pk=pk)
        return is_account_admin(request.user, account)