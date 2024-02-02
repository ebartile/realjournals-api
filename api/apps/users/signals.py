from django.dispatch import Signal
from .models import User
import logging
from django.conf import settings
from django.db.models import F
from django.dispatch import Signal

from django.apps import apps
from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)

@receiver(post_save, sender=User)
def user_post_save(sender, instance, created, **kwargs):
    """
    Populate new account dependen default data
    """
    if not created:
        return

    if instance.is_staff or instance.is_superuser:
        pass