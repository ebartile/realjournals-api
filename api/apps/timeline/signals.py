from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.db import connection

from apps.history import services as history_services
from apps.history.choices import HistoryType
from .service import (push_to_timelines,
                        build_user_namespace,
                        build_account_namespace,
                        extract_user_info)


def _push_to_timelines(account, user, obj, event_type, created_datetime, extra_data={}):
    account_id = None if account is None else account.id

    ct = ContentType.objects.get_for_model(obj)
    if settings.CELERY_ENABLED:
        connection.on_commit(lambda: push_to_timelines.delay(account_id,
                                                             user.id,
                                                             ct.app_label,
                                                             ct.model,
                                                             obj.id,
                                                             event_type,
                                                             created_datetime,
                                                             extra_data=extra_data))
    else:
        push_to_timelines(account_id,
                          user.id,
                          ct.app_label,
                          ct.model,
                          obj.id,
                          event_type,
                          created_datetime,
                          extra_data=extra_data)


def _clean_description_fields(values_diff):
    # Description_diff and description_html if included can be huge, we are
    # removing the html one and clearing the diff
    values_diff.pop("description_html", None)
    if "description_diff" in values_diff:
        values_diff["description_diff"] = _("Check the history API for the exact diff")


def on_new_history_entry(sender, instance, created, **kwargs):
    if instance._importing:
        return

    if instance.is_hidden:
        return None

    if instance.user["pk"] is None:
        return None

    model = history_services.get_model_from_key(instance.key)
    pk = history_services.get_pk_from_key(instance.key)
    obj = model.objects.get(pk=pk)
    account = obj.account

    if instance.type == HistoryType.create:
        event_type = "create"
    elif instance.type == HistoryType.change:
        event_type = "change"
    elif instance.type == HistoryType.delete:
        event_type = "delete"

    user = get_user_model().objects.get(id=instance.user["pk"])
    values_diff = instance.values_diff
    _clean_description_fields(values_diff)

    extra_data = {
        "values_diff": values_diff,
        "user": extract_user_info(user),
        "comment": instance.comment,
        "comment_html": instance.comment_html,
    }

    # Detect deleted comment
    if instance.delete_comment_date:
        extra_data["comment_deleted"] = True

    # Detect edited comment
    if instance.comment_versions is not None and len(instance.comment_versions)>0:
        extra_data["comment_edited"] = True

    created_datetime = instance.created_at
    _push_to_timelines(account, user, obj, event_type, created_datetime, extra_data=extra_data)


def create_membership_push_to_timeline(sender, instance, created, **kwargs):
    """
    Creating new membership with associated user. If the user is the account owner we don't
    do anything because that info will be shown in created account timeline entry

    @param sender: Membership model
    @param instance: Membership object
    """

    # We shown in created account timeline entry
    if created and instance.user and instance.user != instance.account.owner:
        created_datetime = instance.created_at
        _push_to_timelines(instance.account, instance.user, instance, "create", created_datetime)


def delete_membership_push_to_timeline(sender, instance, **kwargs):
    if instance.user:
        created_datetime = timezone.now()
        _push_to_timelines(instance.account, instance.user, instance, "delete", created_datetime)


def create_user_push_to_timeline(sender, instance, created, **kwargs):
    if created:
        account = None
        user = instance
        _push_to_timelines(account, user, user, "create", created_datetime=user.date_joined)