from urllib.parse import urlparse

from django.core.files.storage import default_storage
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.utils.thumbnails import get_thumbnail_url
from apps.users.services import get_user_photo_url, get_user_big_photo_url

from . import models


class TimelineSerializer(serializers.ModelSerializer):
    data = serializers.SerializerMethodField()

    class Meta:
        model = models.Timeline
        fields = ("data", "id", "content_type", "object_id", "namespace", "event_type", "account", "data_content_type", "created",)

    def get_data(self, obj):
        # Updates the data user info saved if the user exists
        if hasattr(obj, "_prefetched_user"):
            user = obj._prefetched_user
        else:
            User = get_user_model()
            userData = obj.data.get("user", None)
            try:
                user = User.objects.get(id=userData["id"])
            except User.DoesNotExist:
                user = None

        if user is not None:
            obj.data["user"] = {
                "id": user.pk,
                "name": user.get_full_name(),
                "photo": get_user_photo_url(user),
                "big_photo": get_user_big_photo_url(user),
                "username": user.username,
                "is_profile_visible": user.is_active and not user.is_system,
                "date_joined": user.date_joined
            }

        if "values_diff" in obj.data and "attachments" in obj.data["values_diff"]:
            [[self.parse_url(item) for item in value] for key, value in
             obj.data["values_diff"]["attachments"].items() if value]

        return obj.data

    def parse_url(self, item):
        if 'attached_file' in item:
            attached_file = item['attached_file']
        else:
            # This is the case for old timeline entries
            file_path = urlparse(item['url']).path
            index = file_path.find('/attachments')
            attached_file = file_path[index+1:]

        item['url'] = default_storage.url(attached_file)

        if 'thumbnail_file' in item:
            thumb_file = item['thumbnail_file']
            thumb_url = default_storage.url(thumb_file) if thumb_file else None
        else:
            thumb_url = get_thumbnail_url(attached_file,
                                          settings.THN_ATTACHMENT_TIMELINE)

        item['thumb_url'] = thumb_url
