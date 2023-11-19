import enum
from django.utils.translation import gettext_lazy as _


class NotifyLevel(enum.IntEnum):
    involved = 1
    all = 2
    none = 3


NOTIFY_LEVEL_CHOICES = (
    (1, _("Involved")),
    (2, _("All")),
    (3, _("None")),
)


class WebNotificationType(enum.IntEnum):
    assigned = 1
    mentioned = 2
    added_as_watcher = 3
    added_as_member = 4
    comment = 5
    mentioned_in_comment = 6


WEB_NOTIFICATION_TYPE_CHOICES = (
    (1, _("Assigned")),
    (2, _("Mentioned")),
    (3, _("Added as watcher")),
    (4, _("Added as member")),
    (5, _("Comment")),
    (6, _("Mentioned in comment")),
)
