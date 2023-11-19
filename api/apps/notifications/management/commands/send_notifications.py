from django.core.management.base import BaseCommand

from apps.notifications.services import send_bulk_email

class Command(BaseCommand):

    def handle(self, *args, **options):
        send_bulk_email()
