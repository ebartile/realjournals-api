from django.apps import apps
from django.contrib.auth import get_user_model

from apps.users.templatetags.functions import resolve_account

from .base import Sitemap


class UsersSitemap(Sitemap):
    def items(self):
        user_model = get_user_model()

        # Only active users and not system users
        queryset = user_model.objects.filter(is_active=True,
                                             is_system=False)

        return queryset

    def location(self, obj):
        return resolve_account("user", obj.username)

    def lastmod(self, obj):
        return None

    def changefreq(self, obj):
        return "weekly"

    def priority(self, obj):
        return 0.5
