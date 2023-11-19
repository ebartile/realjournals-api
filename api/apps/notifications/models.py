import enum
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.fields import GenericForeignKey
from .choices import NotifyLevel, NOTIFY_LEVEL_CHOICES

class NotifyPolicy(models.Model):
    account = models.ForeignKey("accounts.Account", related_name="notify_policies", on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="notify_policies", on_delete=models.CASCADE)
    notify_level = models.SmallIntegerField(choices=NOTIFY_LEVEL_CHOICES)
    live_notify_level = models.SmallIntegerField(choices=NOTIFY_LEVEL_CHOICES, default=NotifyLevel.involved)
    web_notify_level = models.BooleanField(default=True, null=False, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    modified_at = models.DateTimeField()

    class Meta:
        unique_together = ("account", "user",)
        ordering = ["created_at"]

    def save(self, *args, **kwargs):
        if not self.modified_at:
            self.modified_at = timezone.now()

        return super().save(*args, **kwargs)

class WebNotification(models.Model):
    created = models.DateTimeField(default=timezone.now, db_index=True)
    read = models.DateTimeField(default=None, null=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="web_notifications",
        on_delete=models.CASCADE
    )
    event_type = models.PositiveIntegerField()
    data = models.JSONField()


class Watched(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=False,
        null=False,
        related_name="watched",
        verbose_name=_("user"),
        on_delete=models.CASCADE
    )
    account = models.ForeignKey(
        "accounts.Account",
        null=False,
        blank=False,
        verbose_name=_("account"),
        related_name="watched",
        on_delete=models.CASCADE
    )
    created_date = models.DateTimeField(auto_now_add=True, null=False, blank=False,
                                        verbose_name=_("created date"))
    content_type = models.ForeignKey("contenttypes.ContentType", on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")

    class Meta:
        verbose_name = _("Watched")
        verbose_name_plural = _("Watched")
        unique_together = ("content_type", "object_id", "user", "account")