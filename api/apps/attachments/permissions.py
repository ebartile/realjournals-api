from apps.accounts.permissions import PermissionComponent

class IsAttachmentOwnerPerm(PermissionComponent):
    def has_object_permission(self, request, view, obj=None):
        if obj and obj.owner and request.user.is_authenticated:
            return request.user == obj.owner
        return False
