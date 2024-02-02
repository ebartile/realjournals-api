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

    template = getattr(instance, "creation_template", None)
    if template is None:
        AccountTemplate = apps.get_model("accounts", "AccountTemplate")
        template = AccountTemplate.objects.get(slug=settings.DEFAULT_ACCOUNT_TEMPLATE)

    template.apply_to_account(instance)

    instance.save()

    AccountRole = apps.get_model("accounts", "AccountRole")
    try:
        owner_role = instance.roles.get(slug=template.default_owner_role)
    except AccountRole.DoesNotExist:
        owner_role = instance.roles.first()

    if owner_role:
        Membership = apps.get_model("accounts", "Membership")
        member, created = Membership.objects.get_or_create(user=instance.owner, account=instance, role=owner_role)
        member.is_admin=True
        member.save()



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
