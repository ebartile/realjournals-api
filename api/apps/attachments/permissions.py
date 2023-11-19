from apps.history.permissions import PermissionComponent

class IsAttachmentOwnerPerm(PermissionComponent):
    def has_object_permission(self, request, view, obj=None):
        if obj and obj.owner and request.user.is_authenticated:
            return request.user == obj.owner
        return False

class CommentAttachmentPerm(PermissionComponent):
    def has_object_permission(self, request, view, obj=None):
        if obj.from_comment:
            return True
        return False


class RawAttachmentPerm(PermissionComponent):
    def has_object_permission(self, request, view, obj=None):
        is_owner = IsAttachmentOwnerPerm().has_object_permission(request, view, obj)
        if obj.content_type.app_label == "journals" and obj.content_type.model == "journal":
            return HasAccountPerm('view_journal') | IsAttachmentOwnerPerm() or is_owner
        return False
