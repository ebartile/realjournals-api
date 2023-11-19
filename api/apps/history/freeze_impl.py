from contextlib import suppress

from functools import partial
from django.apps import apps
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist

from apps.utils.iterators import as_tuple
from apps.utils.iterators import as_dict
from apps.utils.mdrender.service import render as mdrender

from apps.attachments.services import get_timeline_image_thumbnail_name

import os

####################
# Values
####################


@as_dict
def _get_generic_values(ids: tuple, *, typename=None, attr: str="name") -> tuple:
    app_label, model_name = typename.split(".", 1)
    content_type = ContentType.objects.get(app_label=app_label, model=model_name)
    model_cls = content_type.model_class()

    ids = filter(lambda x: x is not None, ids)
    qs = model_cls.objects.filter(pk__in=ids)
    for instance in qs:
        yield str(instance.pk), getattr(instance, attr)


@as_dict
def _get_users_values(ids: set) -> dict:
    user_model = get_user_model()
    ids = filter(lambda x: x is not None, ids)
    qs = user_model.objects.filter(pk__in=tuple(ids))

    for user in qs:
        yield str(user.pk), user.get_full_name()


@as_dict
def _get_user_story_values(ids: set) -> dict:
    userstory_model = apps.get_model("userstories", "UserStory")
    ids = filter(lambda x: x is not None, ids)
    qs = userstory_model.objects.filter(pk__in=tuple(ids))

    for userstory in qs:
        yield str(userstory.pk), "#{} {}".format(userstory.ref, userstory.subject)


_get_journal_type_values = partial(_get_generic_values, typename="accounts.journaltype")
_get_role_values = partial(_get_generic_values, typename="users.role")

def _common_users_values(diff):
    """
    Groups common values resolver logic of
    journals.
    """
    values = {}
    users = set()

    if "owner" in diff and isinstance(diff["owner"], int):
        users.update(diff["owner"])
    if "assigned_to" in diff:
        users.update(diff["assigned_to"])
    if "assigned_users" in diff:
        [users.update(usrs_ids) for usrs_ids in diff["assigned_users"] if
         usrs_ids]

    user_ids = [user_id for user_id in users if isinstance(user_id, int)]
    values["users"] = _get_users_values(set(user_ids)) if users else {}

    return values


def account_values(diff):
    values = _common_users_values(diff)
    return values


def journal_values(diff):
    values = _common_users_values(diff)

    if "type" in diff:
        values["type"] = _get_journal_type_values(diff["type"])

    return values


####################
# Freezes
####################

def _generic_extract(obj: object, fields: list, default=None) -> dict:
    result = {}
    for fieldname in fields:
        result[fieldname] = getattr(obj, fieldname, default)
    return result


@as_tuple
def extract_attachments(obj) -> list:
    for attach in obj.attachments.all():
        # Force the creation of a thumbnail for the timeline
        thumbnail_file = get_timeline_image_thumbnail_name(attach)

        yield {"id": attach.id,
               "filename": os.path.basename(attach.attached_file.name),
               "url": attach.attached_file.url,
               "attached_file": str(attach.attached_file),
               "thumbnail_file": thumbnail_file,
               "is_deprecated": attach.is_deprecated,
               "description": attach.description,
               "order": attach.order}


@as_tuple
def extract_journal_custom_attributes(obj) -> list:
    with suppress(ObjectDoesNotExist):
        custom_attributes_values = obj.custom_attributes_values.attributes_values
        for attr in obj.account.journalcustomattributes.all():
            with suppress(KeyError):
                value = custom_attributes_values[str(attr.id)]
                yield {"id": attr.id,
                       "name": attr.name,
                       "value": value,
                       "type": attr.type}


def account_freezer(account) -> dict:
    fields = ("name",
              "slug",
              "created_at",
              "owner_id",
              "is_private",
              "anon_permissions",
              "public_permissions",
              "is_journal_activated"
            #   TODO add others
              )
    return _generic_extract(account, fields)

def journal_freezer(journal) -> dict:

    snapshot = {
        "ref": journal.ref,
        "owner": journal.owner_id,
        "type": journal.type_id,
        "description": journal.description,
        "description_html": mdrender(journal.account, journal.description),
        "attachments": extract_attachments(journal),
        "custom_attributes": extract_journal_custom_attributes(journal)
        # TODO add others
    }

    return snapshot
