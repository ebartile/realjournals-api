from django.conf import settings
from django.core.management.base import BaseCommand
from django.test.utils import override_settings

from apps.timeline.models import Timeline
from apps.accounts.models import Account

class Command(BaseCommand):
    help = 'Regenerate unnecessary new memberships entry lines'

    @override_settings(DEBUG=False)
    def handle(self, *args, **options):
        removing_timeline_ids = []
        for t in Timeline.objects.filter(event_type="accounts.membership.create").order_by("created"):
            print(t.created)
            if t.account.owner.id == t.data["user"].get("id", None):
                removing_timeline_ids.append(t.id)

        Timeline.objects.filter(id__in=removing_timeline_ids).delete()
