import enum
from django.utils.translation import gettext_lazy as _

ADMIN_PAGE_CHOICES = (
    ("admin.dashboard", _("Terminal Dashboard")),
)

TERMINAL_PAGE_CHOICES = (
    ("terminal.dashboard", _("Terminal Dashboard")),
    ("terminal.journal", _("Terminal Journal")),
)

TERMINAL_MODULES_CHOICES = (
    ('latest_users', 'Latest Users'),
    ('registration_chart', 'Registration Chart'),
    ('system_status', 'System Status'),
    ('earning_summary', 'Earning Summary')
)

ADMIN_MODULES_CHOICES = (
    ('latest_users', 'Latest Users'),
    ('registration_chart', 'Registration Chart'),
    ('system_status', 'System Status'),
    ('earning_summary', 'Earning Summary')
)