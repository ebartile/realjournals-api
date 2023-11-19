import logging
from celery import shared_task
from .models import Account
from apps.attachments.models import Attachment

logger = logging.getLogger(__name__)

@shared_task
def process_import_task(attachment_id, user_id):
    logger.debug("Processing Attachment:{attachment_id} of User:{user_id}")
    attachment = Attachment.objects.get(id=attachment_id, owner=user_id)
    attachment.status = "done"
    attachment.save()
    account = Account.objects.get(id=attachment.account.id)
    account.has_be_configured=True
    account.save()

