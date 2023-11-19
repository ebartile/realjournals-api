from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

class ActivityLog(models.Model):
    action = models.CharField(max_length=255)
    ip = models.GenericIPAddressField()
    location = models.JSONField()
    agent = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)

    # GenericForeignKey for relating to different models
    content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    def __str__(self):
        return f'{self.action} by {self.content_type} on {self.timestamp}'
