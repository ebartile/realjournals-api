from django.contrib.auth import get_user_model
from apps.utils.exceptions import NotAuthenticated
from django.apps import apps
from django.core import signing
from django.utils.translation import gettext_lazy as _


def get_token_for_user(user, scope):
    """
    Generate a new signed token containing
    a specified user limited for a scope (identified as a string).
    """
    data = {"user_%s_id" % (scope): user.id}
    return signing.dumps(data)


def get_user_for_token(token, scope, max_age=None):
    """
    Given a selfcontained token and a scope try to parse and
    unsign it.

    If max_age is specified it checks token expiration.

    If token passes a validation, returns
    a user instance corresponding with user_id stored
    in the incoming token.
    """
    try:
        data = signing.loads(token, max_age=max_age)
    except signing.BadSignature:
        raise NotAuthenticated(_("Invalid token"))

    model_cls = get_user_model()

    try:
        user = model_cls.objects.get(pk=data["user_%s_id" % (scope)])
    except (model_cls.DoesNotExist, KeyError):
        raise NotAuthenticated(_("Invalid token"))
    else:
        return user
