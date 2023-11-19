from django.utils.translation import gettext_lazy as _

BLOCKED_BY_NONPAYMENT = "blocked-by-nonpayment"
BLOCKED_BY_STAFF = "blocked-by-staff"
BLOCKED_BY_OWNER_LEAVING = "blocked-by-owner-leaving"
BLOCKED_BY_DELETING = "blocked-by-deleting"

BLOCKING_CODES = [
    (BLOCKED_BY_NONPAYMENT, _("This account is blocked due to payment failure")),
    (BLOCKED_BY_STAFF, _("This account is blocked by admin staff")),
    (BLOCKED_BY_OWNER_LEAVING, _("This account is blocked because the owner left")),
    (BLOCKED_BY_DELETING, _("This account is blocked while it's deleted"))
]
