from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.utils import timezone

from apps.events import events
from apps.events import middleware as mw

from . import choices
from . import models
from . import serializers


def _filter_recipients(account, user, recipients):
    notify_policies = models.NotifyPolicy.objects.filter(
        user_id__in=recipients,
        account=account,
        web_notify_level=True).exclude(user_id=user.id).all()
    return [notify_policy.user_id for notify_policy in notify_policies]


def _push_to_web_notifications(event_type, data, recipients,
                               serializer_class=None):
    if not serializer_class:
        serializer_class = serializers.ObjectNotificationSerializer

    serializer = serializer_class(data)
    for user_id in recipients:
        with transaction.atomic():
            models.WebNotification.objects.create(
                event_type=event_type.value,
                created=timezone.now(),
                user_id=user_id,
                data=serializer.data,
            )
        session_id = mw.get_current_session_id()
        events.emit_event_for_user_notification(user_id,
                                                session_id=session_id,
                                                event_type=event_type.value,
                                                data=serializer.data)


def on_assigned_to(sender, user, obj, **kwargs):
    event_type = choices.WebNotificationType.assigned
    data = {
        "account": obj.account,
        "user": user,
        "obj": obj,
    }
    recipients = _filter_recipients(obj.account, user,
                                    [obj.assigned_to.id])
    _push_to_web_notifications(event_type, data, recipients)


def on_assigned_users(sender, user, obj, new_assigned_users, **kwargs):
    event_type = choices.WebNotificationType.assigned
    data = {
        "account": obj.account,
        "user": user,
        "obj": obj,
    }
    recipients = _filter_recipients(obj.account, user,
                                    [user_id for user_id in new_assigned_users])
    _push_to_web_notifications(event_type, data, recipients)


def on_watchers_added(sender, user, obj, new_watchers, **kwargs):
    event_type = choices.WebNotificationType.added_as_watcher
    data = {
        "account": obj.account,
        "user": user,
        "obj": obj,
    }
    recipients = _filter_recipients(obj.account, user, new_watchers)
    _push_to_web_notifications(event_type, data, recipients)


def on_members_added(sender, user, account, new_members, **kwargs):
    serializer_class = serializers.NotificationDataSerializer
    event_type = choices.WebNotificationType.added_as_member
    data = {
        "account": account,
        "user": user,
    }
    recipients = _filter_recipients(account, user,
                                    [member.user_id for member in new_members
                                     if member.user_id])

    _push_to_web_notifications(event_type, data, recipients, serializer_class)


def on_mentions(sender, user, obj, mentions, **kwargs):
    content_type = ContentType.objects.get_for_model(obj)
    valid_content_types = ['task',]
    if content_type.model in valid_content_types:
        event_type = choices.WebNotificationType.mentioned
        data = {
            "account": obj.account,
            "user": user,
            "obj": obj,
        }
        recipients = _filter_recipients(obj.account, user,
                                        [user.id for user in mentions])
        _push_to_web_notifications(event_type, data, recipients)


def on_comment_mentions(sender, user, obj, mentions, **kwargs):
    event_type = choices.WebNotificationType.mentioned_in_comment
    data = {
        "account": obj.account,
        "user": user,
        "obj": obj,
    }
    recipients = _filter_recipients(obj.account, user,
                                    [user.id for user in mentions])
    _push_to_web_notifications(event_type, data, recipients)


def on_comment(sender, user, obj, watchers, **kwargs):
    event_type = choices.WebNotificationType.comment
    data = {
        "account": obj.account,
        "user": user,
        "obj": obj,
    }
    recipients = _filter_recipients(obj.account, user, watchers)
    _push_to_web_notifications(event_type, data, recipients)
