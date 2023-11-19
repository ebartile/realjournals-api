from django.apps import apps
from django.utils.translation import gettext_lazy as _
from apps.utils.exceptions import IntegrityError
from .models import NotifyLevel
from django_pglocks import advisory_lock

def analyze_object_for_watchers(obj: object, comment: str, user: object):
    """
    Generic implementation for analize model objects and
    extract mentions from it and add it to watchers.
    """
    if not hasattr(obj, "add_watcher"):
        return

    # Adding the person who edited the object to the watchers
    if comment and not user.is_system:
        obj.add_watcher(user)

    mentions = get_object_mentions(obj, comment) or []
    for mentioned in mentions:
        obj.add_watcher(mentioned)


def create_notify_policy_if_not_exists(account, user,
                                       level=NotifyLevel.involved,
                                       live_level=NotifyLevel.involved,
                                       web_level=True):
    """
    Given a account and user, create notification policy for it.
    """
    model_cls = apps.get_model("notifications", "NotifyPolicy")
    try:
        result = model_cls.objects.get_or_create(
            account=account,
            user=user,
            defaults={
                "notify_level": level,
                "live_notify_level": live_level,
                "web_notify_level": web_level
            }
        )
        return result[0]
    except IntegrityError as e:
        raise IntegrityError(
            _("Notify exists for specified user and account")) from e

def send_bulk_email():
    with advisory_lock("send-notifications-command", wait=False) as acquired:
        if acquired:
            pass
            # TODO