import logging
from apps.notifications.services import create_notify_policy_if_not_exists
from django.conf import settings
from django.db.models import F
from django.dispatch import Signal

from django.apps import apps
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Account, Membership

logger = logging.getLogger(__name__)

# Define a signal without providing_args

## account attributes
@receiver(post_save, sender=Account)
def account_post_save(sender, instance, created, **kwargs):
    """
    Populate new account dependen default data
    """
    if not created:
        return

    Role = apps.get_model("users", "Role")
    owner_role = Role.objects.get(slug="account-owner")

    logger.info(owner_role)

    if owner_role:
        Membership = apps.get_model("accounts", "Membership")
        Membership.objects.create(user=instance.owner, account=instance, role=owner_role,
                                  is_admin=True)

        # membership_registered.send(sender=Membership.__class__, membership=Membership)


@receiver(post_save, sender=Membership)
def membership_post_save(sender, instance, using, **kwargs):
    if not instance.user:
        return
    create_notify_policy_if_not_exists(instance.account, instance.user)

    # Set account on top on user accounts list
    membership = apps.get_model("accounts", "Membership")
    membership.objects.filter(user=instance.user) \
        .update(user_order=F('user_order') + 1)

    membership.objects.filter(user=instance.user, account=instance.account)\
        .update(user_order=0)
