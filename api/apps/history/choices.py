
import enum

from django.utils.translation import gettext_lazy as _


class HistoryType(enum.IntEnum):
    change = 1
    create = 2
    delete = 3


HISTORY_TYPE_CHOICES = ((HistoryType.change, _("Change")),
                        (HistoryType.create, _("Create")),
                        (HistoryType.delete, _("Delete")))
