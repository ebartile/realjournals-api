"""
Authentication backends for rest framework.

This module exposes two backends: session and token.

The first (session) is a modified version of standard
session authentication backend of restframework with
csrf token disabled.

And the second (token) implements own version of oauth2
like authentication but with selfcontained tokens. Thats
makes authentication totally stateless.

It uses django signing framework for create new
self-contained tokens. This trust tokes from external
fraudulent modifications.
"""

import re

from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from rest_framework.authentication import BaseAuthentication
from django.core import signing
from django.contrib.auth import get_user_model
from rest_framework.exceptions import NotAuthenticated
from django.utils.translation import gettext_lazy as _

class Token(BaseAuthentication):
    """
    Self-contained stateless authentication implementation
    that works similar to oauth2.
    It uses django signing framework for trust data stored
    in the token.
    """

    auth_rx = re.compile(r"^BearerToken (.+)$")

    def authenticate(self, request):
        if "HTTP_AUTHORIZATION" not in request.META:
            return None

        token_rx_match = self.auth_rx.search(request.META["HTTP_AUTHORIZATION"])
        if not token_rx_match:
            return None

        token = token_rx_match.group(1)
        max_age_auth_token = getattr(settings, "MAX_AGE_AUTH_TOKEN", None)

        try:
            data = signing.loads(token, max_age=max_age_auth_token)
        except signing.BadSignature:
            raise NotAuthenticated(_("Invalid token"))

        model_cls = get_user_model()

        try:
            user = model_cls.objects.get(pk=data["user_%s_id" % ("authentication")])
        except (model_cls.DoesNotExist, KeyError):
            raise NotAuthenticated(_("Invalid token"))

        if user.last_login is None or user.last_login < (timezone.now() - timedelta(minutes=1)):
            user.last_login = timezone.now()
            user.save(update_fields=["last_login"])

        return (user, token)

    def authenticate_header(self, request):
        return 'BearerToken realm="api"'
