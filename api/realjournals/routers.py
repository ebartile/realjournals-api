from rest_framework import routers
from django.conf import settings

router = routers.DefaultRouter(trailing_slash=False)

from apps.users.api import AuthViewSet
from apps.users.api import UsersViewSet
from apps.settings.api import AdminPageViewSet

router.register(r"auth", AuthViewSet, basename="auth")
router.register(r"users", UsersViewSet, basename="users")
router.register(r"users/(?P<id>\d+)/admin-pages", AdminPageViewSet, basename="admin-pages")

from apps.accounts.api import AccountViewset, BrokerViewSet, RolesViewSet, MembershipViewSet, InvitationViewSet
from apps.attachments.api import AccountAttachmentsViewSet
from apps.settings.api import TerminalPageViewSet

router.register(r"accounts", AccountViewset, basename="accounts")
router.register(r"accounts/(?P<id>\d+)/attachments", AccountAttachmentsViewSet, basename="account-attachment")
router.register(r"accounts/(?P<id>\d+)/pages", TerminalPageViewSet, basename="account-pages")
router.register(r"accounts/(?P<id>\d+)/roles", RolesViewSet, basename="account-roles")
router.register(r"accounts/(?P<id>\d+)/memberships", MembershipViewSet, basename="memberships")
router.register(r"accounts/(?P<id>\d+)/invitations", InvitationViewSet, basename="invitations")
router.register(r"brokers", BrokerViewSet, basename="brokers")

# Notifications & Notify policies
from apps.notifications.api import NotifyPolicyViewSet
from apps.notifications.api import WebNotificationsViewSet

router.register(r"notify-policies", NotifyPolicyViewSet, basename="notifications")
router.register(r"web-notifications", WebNotificationsViewSet, basename="web-notifications")
router.register(r"web-notifications/set-as-read", WebNotificationsViewSet, basename="web-notifications")
router.register(r"web-notifications/(?P<resource_id>\d+)/set-as-read", WebNotificationsViewSet, basename="web-notifications")


# Timelines
from apps.timeline.api import ProfileTimeline
from apps.timeline.api import UserTimeline
from apps.timeline.api import AccountTimeline

router.register(r"timeline/profile", ProfileTimeline, basename="profile-timeline")
router.register(r"timeline/user", UserTimeline, basename="user-timeline")
router.register(r"timeline/account", AccountTimeline, basename="account-timeline")

from apps.stats.api import StatisticsViewSet

router.register(r"statistics", StatisticsViewSet, basename="statistics")

from apps.feedback.api import FeedbackViewSet

if settings.FEEDBACK_ENABLED:
    router.register(r"feedback", FeedbackViewSet, basename="feedback")

# Locales
from apps.utils.api import LocalesViewSet
from apps.utils.api import ConfigViewSet

router.register(r"config", ConfigViewSet, basename="config")
router.register(r"locales", LocalesViewSet, basename="locales")

# Account settings
from apps.settings.api import ThemeSettingsViewSet

router.register(r"theme", ThemeSettingsViewSet, basename="theme-settings")

from apps.utils.api import LogEntryViewSet

router.register(r"system-logs", LogEntryViewSet, basename="system-logs")


