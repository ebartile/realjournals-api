from django.apps import apps
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.db.models import Model
from django.db.models import Q
from django.db.models.query import QuerySet

from functools import partial, wraps

from apps.utils.db import get_typename_for_model_class
from realjournals.celery import app

_timeline_impl_map = {}


def _get_impl_key_from_model(model: Model, event_type: str):
    if issubclass(model, Model):
        typename = get_typename_for_model_class(model)
        return _get_impl_key_from_typename(typename, event_type)
    raise Exception("Not valid model parameter")


def _get_impl_key_from_typename(typename: str, event_type: str):
    if isinstance(typename, str):
        return "{0}.{1}".format(typename, event_type)
    raise Exception("Not valid typename parameter")


def build_user_namespace(user: object):
    return "{0}:{1}".format("user", user.id)


def build_account_namespace(account: object):
    return "{0}:{1}".format("account", account.id)


def _add_to_object_timeline(obj: object, instance: object, event_type: str, created_datetime: object,
                            namespace: str="default", extra_data: dict={}):
    assert isinstance(obj, Model), "obj must be a instance of Model"
    assert isinstance(instance, Model), "instance must be a instance of Model"
    from .models import Timeline
    event_type_key = _get_impl_key_from_model(instance.__class__, event_type)
    impl = _timeline_impl_map.get(event_type_key, None)

    account = None
    if hasattr(instance, "account"):
        account = instance.account

    Timeline.objects.create(
        content_object=obj,
        namespace=namespace,
        event_type=event_type_key,
        account=account,
        data=impl(instance, extra_data=extra_data),
        data_content_type=ContentType.objects.get_for_model(instance.__class__),
        created=created_datetime,
    )


def _add_to_objects_timeline(objects, instance: object, event_type: str, created_datetime: object,
                             namespace: str="default", extra_data: dict={}):
    for obj in objects:
        _add_to_object_timeline(obj, instance, event_type, created_datetime, namespace, extra_data)


def _push_to_timeline(objects, instance: object, event_type: str, created_datetime: object,
                      namespace: str="default", extra_data: dict={}):
    if isinstance(objects, Model):
        _add_to_object_timeline(objects, instance, event_type, created_datetime, namespace, extra_data)
    elif isinstance(objects, QuerySet) or isinstance(objects, list):
        _add_to_objects_timeline(objects, instance, event_type, created_datetime, namespace, extra_data)
    else:
        raise Exception("Invalid objects parameter")


@app.task
def push_to_timelines(account_id, user_id, obj_app_label, obj_model_name, obj_id, event_type,
                      created_datetime, extra_data={}):

    ObjModel = apps.get_model(obj_app_label, obj_model_name)
    try:
        obj = ObjModel.objects.get(id=obj_id)
    except ObjModel.DoesNotExist:
        return

    try:
        user = get_user_model().objects.get(id=user_id)
    except get_user_model().DoesNotExist:
        return

    if account_id is not None:
        # Actions related with a account

        accountModel = apps.get_model("accounts", "Account")
        try:
            account = accountModel.objects.get(id=account_id)
        except accountModel.DoesNotExist:
            return

        # account timeline
        _push_to_timeline(account, obj, event_type, created_datetime,
                          namespace=build_account_namespace(account),
                          extra_data=extra_data)

        if hasattr(obj, "get_related_people"):
            related_people = obj.get_related_people()

            _push_to_timeline(related_people, obj, event_type, created_datetime,
                              namespace=build_user_namespace(user),
                              extra_data=extra_data)
    else:
        # Actions not related with a account
        # - Me
        _push_to_timeline(user, obj, event_type, created_datetime,
                          namespace=build_user_namespace(user),
                          extra_data=extra_data)


def get_timeline(obj, namespace=None):
    assert isinstance(obj, Model), "obj must be a instance of Model"
    from .models import Timeline

    ct = ContentType.objects.get_for_model(obj.__class__)
    timeline = Timeline.objects.filter(content_type=ct)

    if namespace is not None:
        timeline = timeline.filter(namespace=namespace)
    else:
        timeline = timeline.filter(object_id=obj.pk)

    timeline = timeline.order_by("-created")
    return timeline


def filter_timeline_for_user(timeline, user):
    # Superusers can see everything
    if user.is_superuser:
        return timeline

    # Filtering entities from public accounts or entities without account
    tl_filter = Q(account__is_private=False) | Q(account=None)

    # Filtering private account with some public parts
    content_types = {
        "view_account": ContentType.objects.get_by_natural_key("accounts", "account"),
        "view_journal": ContentType.objects.get_by_natural_key("journals", "journal")
    }

    for content_type_key, content_type in content_types.items():
        tl_filter |= Q(account__is_private=True,
                       account__anon_permissions__contains=[content_type_key],
                       data_content_type=content_type)

    # There is no specific permission for seeing new memberships
    membership_content_type = ContentType.objects.get_by_natural_key(app_label="accounts", model="membership")
    tl_filter |= Q(account__is_private=True,
                   account__anon_permissions__contains=["view_account"],
                   data_content_type=membership_content_type)

    # Filtering private accounts where user is member
    if not user.is_anonymous:
        for membership in user.cached_memberships:
            # Admin roles can see everything in a account
            if membership.is_admin:
                tl_filter |= Q(account=membership.account)
            else:
                data_content_types = list(filter(None, [content_types.get(a, None) for a in
                                                        membership.role.permissions]))
                data_content_types.append(membership_content_type)
                tl_filter |= Q(account=membership.account, data_content_type__in=data_content_types)

    timeline = timeline.filter(tl_filter)
    return timeline


def get_profile_timeline(user, accessing_user=None):
    timeline = get_timeline(user)
    if accessing_user is not None:
        timeline = filter_timeline_for_user(timeline, accessing_user)
    return timeline


def get_user_timeline(user, accessing_user=None):
    namespace = build_user_namespace(user)
    timeline = get_timeline(user, namespace)
    if accessing_user is not None:
        timeline = filter_timeline_for_user(timeline, accessing_user)
    return timeline


def get_account_timeline(account, accessing_user=None):
    namespace = build_account_namespace(account)
    timeline = get_timeline(account, namespace)
    if accessing_user is not None:
        timeline = filter_timeline_for_user(timeline, accessing_user)
    return timeline


def register_timeline_implementation(typename: str, event_type: str, fn=None):
    assert isinstance(typename, str), "typename must be a string"
    assert isinstance(event_type, str), "event_type must be a string"

    if fn is None:
        return partial(register_timeline_implementation, typename, event_type)

    @wraps(fn)
    def _wrapper(*args, **kwargs):
        return fn(*args, **kwargs)

    key = _get_impl_key_from_typename(typename, event_type)

    _timeline_impl_map[key] = _wrapper
    return _wrapper


def extract_account_info(instance):
    return {
        "id": instance.pk,
        "slug": instance.slug,
        "name": instance.name,
        "description": instance.description,
    }


def extract_user_info(instance):
    return {
        "id": instance.pk
    }


def extract_journal_info(instance):
    return {
        "id": instance.pk,
        "ref": instance.ref,
        "subject": instance.subject,
    }


def extract_role_info(instance):
    return {
        "id": instance.pk,
        "name": instance.name,
    }
