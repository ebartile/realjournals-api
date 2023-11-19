from django.db.models import Q
from django.apps import apps

from apps.users.templatetags.functions import resolve_terminal
from datetime import timedelta
from django.utils import timezone

from .base import Sitemap


class AccountsSitemap(Sitemap):
    def items(self):
        account_model = apps.get_model("accounts", "Account")

        # Get public accounts OR private accounts if anon user can view them
        queryset = account_model.objects.filter(Q(is_private=False) |
                                                Q(is_private=True,
                                                  anon_permissions__contains=["view_account"]))

        # Exclude blocked accounts
        queryset = queryset.filter(blocked_code__isnull=True)
        queryset = queryset.exclude(description="")
        queryset = queryset.exclude(description__isnull=True)

        return queryset

    def location(self, obj):
        return resolve_terminal("account", obj.slug)

    def lastmod(self, obj):
        return obj.modified_date

    def changefreq(self, obj):
        if (timezone.now() - obj.modified_date) > timedelta(days=30):
            return "monthly"
        return "daily"

    def priority(self, obj):
        return 0.8

