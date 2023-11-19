from django.db import models
from django.utils import timezone

from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

from apps.accounts.models import Account


class Timeline(models.Model):
    content_type = models.ForeignKey(ContentType, related_name="content_type_timelines", on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    namespace = models.CharField(max_length=250, default="default", db_index=True)
    event_type = models.CharField(max_length=250, db_index=True)
    account = models.ForeignKey(Account, null=True, on_delete=models.CASCADE)
    data = models.JSONField()
    data_content_type = models.ForeignKey(ContentType, related_name="data_timelines", on_delete=models.CASCADE)
    created = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=['namespace', '-created']),
            models.Index(fields=['content_type', 'object_id', '-created']),
        ]


# Register all implementations
from .timeline_implementations import *

# Register all signals
from .signals import *
