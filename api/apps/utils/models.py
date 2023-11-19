from django.db import models
from django.utils import timezone

class LogEntry(models.Model):
    level = models.CharField(max_length=10)
    message = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField()
    seen_at = models.BooleanField(default=False, null=False, blank=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.level} - {self.created_at}"

    def save(self, *args, **kwargs):
        if not self.updated_at:
            self.updated_at = timezone.now()

        return super().save(*args, **kwargs)

