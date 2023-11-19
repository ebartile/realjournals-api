from django.db import models
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

from apps.accounts.models import Account
from apps.journals.models import Journal

from . import sequences as seq


class Reference(models.Model):
    content_type = models.ForeignKey(ContentType, related_name="+", on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    ref = models.BigIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")
    created_at = models.DateTimeField(default=timezone.now)
    account = models.ForeignKey(
        "accounts.Account",
        null=False,
        blank=False,
        related_name="references",
        on_delete=models.CASCADE,
    )

    class Meta:
        ordering = ["created_at"]
        unique_together = ["account", "ref"]

    def __str__(self):
        return "Reference {}".format(self.object_id)


def make_sequence_name(account) -> str:
    return "references_account{0}".format(account.pk)


def make_unique_reference_id(account, *, create=False):
    seqname = make_sequence_name(account)
    if create and not seq.exists(seqname):
        seq.create(seqname)
    return seq.next_value(seqname)


def make_reference(instance, account, create=False):
    refval = make_unique_reference_id(account, create=create)
    ct = ContentType.objects.get_for_model(instance.__class__)
    refinstance = Reference.objects.create(content_type=ct,
                                           object_id=instance.pk,
                                           ref=refval,
                                           account=account)
    return refval, refinstance


def recalc_reference_counter(account):
    seqname = make_sequence_name(account)
    max_ref_journal = account.journals.all().aggregate(max=models.Max('ref'))
    max_references = list(filter(lambda x: x is not None, [max_ref_us['max'], max_ref_task['max'], max_ref_journal['max']]))

    max_value = 0
    if len(max_references) > 0:
        max_value = max(max_references)
    seq.set_max(seqname, max_value)


def create_sequence(sender, instance, created, **kwargs):
    if not created:
        return

    seqname = make_sequence_name(instance)
    if not seq.exists(seqname):
        seq.create(seqname)


def delete_sequence(sender, instance, **kwargs):
    seqname = make_sequence_name(instance)
    if seq.exists(seqname):
        seq.delete(seqname)


def store_previous_account(sender, instance, **kwargs):
    try:
        prev_instance = sender.objects.get(pk=instance.pk)
        instance.prev_account = prev_instance.account
    except sender.DoesNotExist:
        instance.prev_account = None


def attach_sequence(sender, instance, created, **kwargs):
    if not instance._importing:
        if created or instance.prev_account != instance.account:
            # Create a reference object. This operation should be
            # used in transaction context, otherwise it can
            # create a lot of phantom reference objects.
            refval, _ = make_reference(instance, instance.account)

            # Additionally, attach sequence number to instance as ref
            instance.ref = refval
            instance.save(update_fields=['ref'])


# account
models.signals.post_save.connect(create_sequence, sender=Account, dispatch_uid="refaccount")
models.signals.post_delete.connect(delete_sequence, sender=Account, dispatch_uid="refaccountdel")

# journal
models.signals.pre_save.connect(store_previous_account, sender=Journal, dispatch_uid="refjournal")
models.signals.post_save.connect(attach_sequence, sender=Journal, dispatch_uid="refjournal")
