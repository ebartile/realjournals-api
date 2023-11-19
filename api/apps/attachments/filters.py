from apps.users.filters import PermissionBasedFilterBackend

#####################################################################
# Attachments filters
#####################################################################

class PermissionBasedAttachmentFilterBackend(PermissionBasedFilterBackend):
    permission = None

    def filter_queryset(self, request, queryset, view):
        qs = super().filter_queryset(request, queryset, view)

        ct = view.get_content_type()
        return qs.filter(content_type=ct)

class CanViewJournalAttachmentFilterBackend(PermissionBasedAttachmentFilterBackend):
    permission = "view_journal"
