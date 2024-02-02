import collections

from django.db import connection
from django.utils.translation import gettext_lazy as _

from django.conf import settings

from apps.utils import json
from apps.utils.db import get_typename_for_model_instance
from . import middleware as mw
from . import backends
from apps.users.templatetags.functions import resolve_terminal

def emit_event(data:dict, routing_key:str, *,
               sessionid:str=None, channel:str="events",
               on_commit:bool=True):
    if not sessionid:
        sessionid = mw.get_current_session_id()

    data = {"session_id": sessionid,
            "data": data}

    backend = backends.get_events_backend()

    def backend_emit_event():
        backend.emit_event(message=json.dumps(data), routing_key=routing_key, channel=channel)

    if on_commit:
        connection.on_commit(backend_emit_event)
    else:
        backend_emit_event()


def emit_event_for_model(obj, *, type:str="change", channel:str="events",
                         content_type:str=None, sessionid:str=None):
    """
    Sends a model change event.

        type: create | change | delete
    """
    if hasattr(obj, "_importing") and obj._importing:
        return None

    if hasattr(obj, "_excluded_events") and type in obj.excluded_events:
        return None

    assert type in set(["create", "change", "delete"])
    assert hasattr(obj, "account_id")

    if not content_type:
        content_type = get_typename_for_model_instance(obj)

    accountid = getattr(obj, "account_id")
    pk = getattr(obj, "pk", None)

    app_name, model_name = content_type.split(".", 1)
    routing_key = "changes.account.{0}.{1}".format(accountid, app_name)

    if app_name in settings.INSTALLED_APPS:
        routing_key = "%s.%s" % (routing_key, model_name)

    data = {"type": type,
            "matches": content_type,
            "pk": pk}

    return emit_event(routing_key=routing_key,
                      channel=channel,
                      sessionid=sessionid,
                      data=data)


def emit_event_for_user_notification(user_id,
                                     *,
                                     session_id: str=None,
                                     event_type: str=None,
                                     data: dict=None):
    """
    Sends a user notification event.
    """
    return emit_event(
        data,
        "web_notifications.{}".format(user_id),
        sessionid=session_id
    )


def emit_event_for_ids(ids, content_type:str, accountid:int, *,
                       type:str="change", channel:str="events", sessionid:str=None):
    assert type in set(["create", "change", "delete"])
    assert isinstance(ids, collections.Iterable)
    assert content_type, "'content_type' parameter is mandatory"

    app_name, model_name = content_type.split(".", 1)
    routing_key = "changes.account.{0}.{1}".format(accountid, app_name)

    data = {"type": type,
            "matches": content_type,
            "pk": ids}

    return emit_event(routing_key=routing_key,
                      channel=channel,
                      sessionid=sessionid,
                      data=data)
