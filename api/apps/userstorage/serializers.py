from rest_framework import serializers
from . import models


class StorageEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.StorageEntry
        fields = ("key", "value", "created_date", "modified_date")
        read_only_fields = ("created_date", "modified_date")
