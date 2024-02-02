from django.core.management.base import BaseCommand, CommandError
from django.apps import apps
from django.conf import settings

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--account_id',
                            action='store_true',
                            dest='account_id',
                            default=None,
                            help='Provide Account ID')

    def handle(self, *args, **options):
        Account = apps.get_model("accounts", "Account")
        
        if options["account_id"] is not None:
            instance = Account.objects.filter(id=options["account_id"]).first()
            template = getattr(instance, "creation_template", None)
            if template is None:
                AccountTemplate = apps.get_model("accounts", "AccountTemplate")
                template = AccountTemplate.objects.get(slug=settings.DEFAULT_ACCOUNT_TEMPLATE)

            template.apply_to_account(instance)

            instance.save()
        else:
            accounts = Account.objects.all()

            for instance in accounts:
                template = getattr(instance, "creation_template", None)
                if template is None:
                    AccountTemplate = apps.get_model("accounts", "AccountTemplate")
                    template = AccountTemplate.objects.get(slug=settings.DEFAULT_ACCOUNT_TEMPLATE)

                template.apply_to_account(instance)

                instance.save()

