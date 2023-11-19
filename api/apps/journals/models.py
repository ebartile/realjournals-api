from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation

TEXT_TYPE = "text"
MULTILINE_TYPE = "multiline"
RICHTEXT_TYPE = "richtext"
DATE_TYPE = "date"
URL_TYPE = "url"
DROPDOWN_TYPE = "dropdown"
CHECKBOX_TYPE = "checkbox"
NUMBER_TYPE = "number"

TYPES_CHOICES = (
    (TEXT_TYPE, _("Text")),
    (MULTILINE_TYPE, _("Multi-Line Text")),
    (RICHTEXT_TYPE, _("Rich text")),
    (DATE_TYPE, _("Date")),
    (URL_TYPE, _("Url")),
    (DROPDOWN_TYPE, _("Dropdown")),
    (CHECKBOX_TYPE, _("Checkbox")),
    (NUMBER_TYPE, _("Number")),
)

class AbstractCustomAttribute(models.Model):
    name = models.CharField(null=False, blank=False, max_length=64, verbose_name=_("name"))
    description = models.TextField(null=False, blank=True, verbose_name=_("description"))
    type = models.CharField(null=False, blank=False, max_length=16,
                            choices=TYPES_CHOICES, default=TEXT_TYPE,
                            verbose_name=_("type"))
    order = models.BigIntegerField(null=False, blank=False, verbose_name=_("order"))
    account = models.ForeignKey(
        "accounts.Account",
        null=False,
        blank=False,
        related_name="%(class)ss",
        verbose_name=_("account"),
        on_delete=models.CASCADE,
    )
    extra = models.JSONField(blank=True, default=None, null=True)
    created_date = models.DateTimeField(null=False, blank=False, default=timezone.now,
                                        verbose_name=_("created date"))
    modified_date = models.DateTimeField(null=False, blank=False,
                                         verbose_name=_("modified date"))

    class Meta:
        abstract = True
        ordering = ["account", "order", "name"]
        unique_together = ("account", "name")

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.modified_date:
            self.modified_date = timezone.now()

        return super().save(*args, **kwargs)

class JournalCustomAttribute(AbstractCustomAttribute):
    class Meta(AbstractCustomAttribute.Meta):
        verbose_name = "journal custom attribute"
        verbose_name_plural = "journal custom attributes"

######################################################
#  Custom Attributes Values Models
#######################################################

class AbstractCustomAttributesValues(models.Model):
    attributes_values = models.JSONField(null=False, blank=False, default=dict, verbose_name=_("values"))

    class Meta:
        abstract = True
        ordering = ["id"]

class JournalCustomAttributesValues(AbstractCustomAttributesValues):
    journal = models.OneToOneField(
        "journals.Journal",
        null=False,
        blank=False,
        related_name="custom_attributes_values",
        verbose_name=_("journal"),
        on_delete=models.CASCADE,
    )

    class Meta(AbstractCustomAttributesValues.Meta):
        verbose_name = "journal custom attributes values"
        verbose_name_plural = "journal custom attributes values"
        index_together = [("journal",)]

    @property
    def account(self):
        # NOTE: This property simplifies checking permissions
        return self.journal.account

class Journal(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        default=None,
        related_name="owned_journals",
        verbose_name=_("owner"),
        on_delete=models.SET_NULL,
    )
    account = models.ForeignKey(
        "accounts.Account",
        null=False,
        blank=False,
        related_name="journals",
        verbose_name=_("account"),
        on_delete=models.CASCADE,
    )
    description = models.TextField(blank=True, verbose_name=_("How did you feel during this trade?"))
    created_date = models.DateTimeField(null=False, blank=False,
                                        verbose_name=_("created date"),
                                        default=timezone.now)
    modified_date = models.DateTimeField(null=False, blank=False,
                                         verbose_name=_("modified date"))
    attachments = GenericRelation("attachments.Attachment")

    class Meta:
        verbose_name = "journal"
        verbose_name_plural = "journals"
        ordering = ["account", "-id"]

    def save(self, *args, **kwargs):
        if not self.modified_date:
            self.modified_date = timezone.now()

        return super().save(*args, **kwargs)

