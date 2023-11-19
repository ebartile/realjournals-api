from django.core.management.base import BaseCommand
from django.test.utils import override_settings
from django.core.management import call_command

from apps.accounts.models import Account


class Command(BaseCommand):
    help = 'Regenerate accounts timeline iterating per account'

    @override_settings(DEBUG=False)
    def handle(self, *args, **options):
        total = Account.objects.count()

        for count,account in enumerate(Account.objects.order_by("id")):
            print("***********************************\n",
                  " {}/{} {}\n".format(count+1, total, account.name),
                  "***********************************")
            call_command("rebuild_timeline", account=account.id)
