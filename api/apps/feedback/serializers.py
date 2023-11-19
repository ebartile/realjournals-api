from rest_framework import serializers
from . import models


class FeedbackEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.FeedbackEntry
        fields = "__all__"
        read_only_fields = ("created_date", "email", "full_name",)
