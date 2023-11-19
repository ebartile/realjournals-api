import logging
from collections import namedtuple
from copy import deepcopy
from functools import partial
from functools import wraps

from django.conf import settings
from django.contrib.auth import get_user_model
from django.apps import apps
from django.db import transaction as tx
from django_pglocks import advisory_lock

from apps.utils.mdrender.service import render as mdrender
from apps.utils.db import get_typename_for_model_class
from apps.utils.diff import make_diff as make_diff_from_dicts

from .models import HistoryType

# Freeze implementatitions
from .freeze_impl import account_freezer
from .freeze_impl import journal_freezer

from .freeze_impl import account_values
from .freeze_impl import journal_values

# Type that represents a freezed object
FrozenObj = namedtuple("FrozenObj", ["key", "snapshot"])
FrozenDiff = namedtuple("FrozenDiff", ["key", "diff", "snapshot"])

# Dict containing registred contentypes with their freeze implementation.
_freeze_impl_map = {}

# Dict containing registred containing with their values implementation.
_values_impl_map = {}

# Not important fields for models (history entries with only
# this fields are marked as hidden).
_not_important_fields = {

}

_deprecated_fields = {

}

log = logging.getLogger("history")


def make_key_from_model_object(obj: object) -> str:
    """
    Create unique key from model instance.
    """
    tn = get_typename_for_model_class(obj.__class__)
    return "{0}:{1}".format(tn, obj.pk)


def get_model_from_key(key: str) -> object:
    """
    Get model from key
    """
    class_name, pk = key.split(":", 1)
    return apps.get_model(class_name)


def get_pk_from_key(key: str) -> object:
    """
    Get pk from key
    """
    class_name, pk = key.split(":", 1)
    return pk


def get_instance_from_key(key: str) -> object:
    """
    Get instance from key
    """
    model = get_model_from_key(key)
    pk = get_pk_from_key(key)
    try:
        obj = model.objects.get(pk=pk)
        return obj
    except model.DoesNotExist:
        # Catch simultaneous DELETE request
        return None


def register_values_implementation(typename: str, fn=None):
    """
    Register values implementation for specified typename.
    This function can be used as decorator.
    """

    assert isinstance(typename, str), "typename must be specied"

    if fn is None:
        return partial(register_values_implementation, typename)

    @wraps(fn)
    def _wrapper(*args, **kwargs):
        return fn(*args, **kwargs)

    _values_impl_map[typename] = _wrapper
    return _wrapper


def register_freeze_implementation(typename: str, fn=None):
    """
    Register freeze implementation for specified typename.
    This function can be used as decorator.
    """

    assert isinstance(typename, str), "typename must be specied"

    if fn is None:
        return partial(register_freeze_implementation, typename)

    @wraps(fn)
    def _wrapper(*args, **kwargs):
        return fn(*args, **kwargs)

    _freeze_impl_map[typename] = _wrapper
    return _wrapper


# Low level api

def freeze_model_instance(obj: object) -> FrozenObj:
    """
    Creates a new frozen object from model instance.

    The freeze process consists on converting model
    instances to hashable plain python objects and
    wrapped into FrozenObj.
    """

    model_cls = obj.__class__

    # Additional query for test if object is really exists
    # on the database or it is removed.
    try:
        obj = model_cls.objects.get(pk=obj.pk)
    except model_cls.DoesNotExist:
        return None

    typename = get_typename_for_model_class(model_cls)
    if typename not in _freeze_impl_map:
        raise RuntimeError("No implementation found for {}".format(typename))

    key = make_key_from_model_object(obj)
    impl_fn = _freeze_impl_map[typename]
    snapshot = impl_fn(obj)
    assert isinstance(snapshot, dict), \
        "freeze handlers should return always a dict"

    return FrozenObj(key, snapshot)


def is_hidden_snapshot(obj: FrozenDiff) -> bool:
    """
    Check if frozen object is considered
    hidden or not.
    """
    content_type, pk = obj.key.rsplit(":", 1)
    snapshot_fields = frozenset(obj.diff.keys())

    if content_type not in _not_important_fields:
        return False

    nfields = _not_important_fields[content_type]
    result = snapshot_fields - nfields

    if snapshot_fields and len(result) == 0:
        return True

    return False


def get_excluded_fields(typename: str) -> tuple:
    """
    Get excluded and deprected fields to avoid in the diff
    """
    return _deprecated_fields.get(typename, ())


def make_diff(oldobj: FrozenObj, newobj: FrozenObj,
              excluded_keys: tuple = ()) -> FrozenDiff:
    """
    Compute a diff between two frozen objects.
    """
    assert isinstance(newobj, FrozenObj), \
        "newobj parameter should be instance of FrozenObj"

    if oldobj is None:
        return FrozenDiff(newobj.key, {}, newobj.snapshot)

    first = oldobj.snapshot
    second = newobj.snapshot

    diff = make_diff_from_dicts(first, second, None, excluded_keys)

    return FrozenDiff(newobj.key, diff, newobj.snapshot)


def make_diff_values(typename: str, fdiff: FrozenDiff) -> dict:
    """
    Given a typename and diff, build a values dict for it.
    If no implementation found for typename, warnig is raised in
    logging and returns empty dict.
    """

    if typename not in _values_impl_map:
        log.warning(
            "No implementation found of '{}' for values.".format(typename))
        return {}

    impl_fn = _values_impl_map[typename]
    return impl_fn(fdiff.diff)


def _rebuild_snapshot_from_diffs(keysnapshot, partials):
    result = deepcopy(keysnapshot)

    for part in partials:
        for key, value in part.diff.items():
            result[key] = value[1]

    return result


def get_last_snapshot_for_key(key: str) -> FrozenObj:
    entry_model = apps.get_model("history", "HistoryEntry")

    # Search last snapshot
    qs = (entry_model.objects
          .filter(key=key, is_snapshot=True)
          .order_by("-created_at"))

    keysnapshot = qs.first()
    if keysnapshot is None:
        return None, True

    # Get all partial snapshots
    entries = tuple(entry_model.objects
                    .filter(key=key, is_snapshot=False)
                    .filter(created_at__gte=keysnapshot.created_at)
                    .order_by("created_at"))

    snapshot = _rebuild_snapshot_from_diffs(keysnapshot.snapshot, entries)
    max_partial_diffs = getattr(settings, "MAX_PARTIAL_DIFFS", 60)

    if len(entries) >= max_partial_diffs:
        return FrozenObj(keysnapshot.key, snapshot), True

    return FrozenObj(keysnapshot.key, snapshot), False


# Public api

def get_modified_fields(obj: object, last_modifications):
    """
    Get the modified fields for an object through his last modifications
    """
    key = make_key_from_model_object(obj)
    entry_model = apps.get_model("history", "HistoryEntry")
    history_entries = (
        entry_model.objects.filter(key=key)
                           .order_by("-created_at")
                           .values_list("diff",
                                        flat=True)[0:last_modifications]
    )

    modified_fields = []
    for history_entry in history_entries:
        modified_fields += history_entry.keys()

    return modified_fields


@tx.atomic
def take_snapshot(obj: object, *, comment: str="", user=None,
                  delete: bool=False):
    """
    Given any model instance with registred content type,
    create new history entry of "change" type.

    This raises exception in case of object wasn't
    previously freezed.
    """

    key = make_key_from_model_object(obj)
    with advisory_lock("history-"+key):
        typename = get_typename_for_model_class(obj.__class__)

        new_fobj = freeze_model_instance(obj)
        old_fobj, need_real_snapshot = get_last_snapshot_for_key(key)

        entry_model = apps.get_model("history", "HistoryEntry")
        user_id = None if user is None else user.id
        user_name = "" if user is None else user.get_full_name()

        # Determine history type
        if delete:
            entry_type = HistoryType.delete
            need_real_snapshot = True
        elif new_fobj and not old_fobj:
            entry_type = HistoryType.create
        elif new_fobj and old_fobj:
            entry_type = HistoryType.change
        else:
            raise RuntimeError("Unexpected condition")

        excluded_fields = get_excluded_fields(typename)

        fdiff = make_diff(old_fobj, new_fobj, excluded_fields)

        # If diff and comment are empty, do
        # not create empty history entry
        if (not fdiff.diff and
                not comment and old_fobj is not None and
                entry_type != HistoryType.delete):
            return None

        fvals = make_diff_values(typename, fdiff)

        if len(comment) > 0:
            is_hidden = False
        else:
            is_hidden = is_hidden_snapshot(fdiff)

        kwargs = {
            "user": {"pk": user_id, "name": user_name},
            "account_id": getattr(obj, 'account_id', getattr(obj, 'id', None)),
            "key": key,
            "type": entry_type,
            "snapshot": fdiff.snapshot if need_real_snapshot else None,
            "diff": fdiff.diff,
            "values": fvals,
            "comment": comment,
            "comment_html": mdrender(obj.account, comment),
            "is_hidden": is_hidden,
            "is_snapshot": need_real_snapshot,
        }

        return entry_model.objects.create(**kwargs)


# High level query api

def get_history_queryset_by_model_instance(obj: object,
                                           types=(HistoryType.change,),
                                           include_hidden=False):
    """
    Get one page of history for specified object.
    """
    key = make_key_from_model_object(obj)
    history_entry_model = apps.get_model("history", "HistoryEntry")

    qs = history_entry_model.objects.filter(key=key, type__in=types)
    if not include_hidden:
        qs = qs.filter(is_hidden=False)

    return qs.order_by("created_at")


def prefetch_owners_in_history_queryset(qs):
    user_ids = [u["pk"] for u in qs.values_list("user", flat=True)]
    users = get_user_model().objects.filter(id__in=user_ids)
    users_by_id = {u.id: u for u in users}
    for history_entry in qs:
        history_entry.prefetch_owner(users_by_id.get(history_entry.user["pk"],
                                                     None))

    return qs


# Freeze & value register
register_freeze_implementation("accounts.account", account_freezer)
register_freeze_implementation("journals.journal", journal_freezer)

register_values_implementation("accounts.account", account_values)
register_values_implementation("journals.journal", journal_values)
