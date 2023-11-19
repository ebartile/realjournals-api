from django.db.models import Q
from django.apps import apps
from datetime import timedelta
from django.utils import timezone

from apps.users.templatetags.functions import resolve_terminal

from .base import Sitemap


class JournalsSitemap(Sitemap):
    def items(self):
        issue_model = apps.get_model("journals", "Journal")

        # Get journals of public accounts OR private accounts if anon user can view them
        queryset = issue_model.objects.filter(Q(account__is_private=False) |
                                              Q(account__is_private=True,
                                                account__anon_permissions__contains=["view_journals"]))

        # Exclude blocked accounts
        queryset = queryset.filter(account__blocked_code__isnull=True)

        # account data is needed
        queryset = queryset.select_related("account")

        return queryset

    def location(self, obj):
        return resolve_terminal("issue", obj.account.slug, obj.ref)

    def lastmod(self, obj):
        return obj.modified_date

    def changefreq(self, obj):
        if (timezone.now() - obj.modified_date) > timedelta(days=90):
            return "monthly"
        return "weekly"

    def priority(self, obj):
        return 0.5
