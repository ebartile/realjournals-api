from django.conf import settings

from rest_framework import serializers
from apps.utils.thumbnails import get_thumbnail_url

from . import services
from .models import Attachment

class AttachmentValidator(serializers.ModelSerializer):
    attached_file = serializers.FileField(required=True)

    class Meta:
        model = Attachment
        fields = ["id", "account", "owner", "name", "attached_file", "size",
                  "description", "is_deprecated", "created_date",
                  "modified_date", "object_id", "order", "sha1", "from_comment"]
        read_only_fields = ["owner", "created_date", "modified_date", "sha1"]

class AttachmentSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    thumbnail_card_url = serializers.SerializerMethodField()
    preview_url = serializers.SerializerMethodField()

    class Meta:
        model = Attachment
        fields = ["id", "account", "owner", "name", "attached_file", "size", "url", "description", "is_deprecated", "from_comment", "created_date", "modified_date", "object_id", "order", "sha1", "url", "thumbnail_card_url", "preview_url", "status"]
        read_only_fields = ["owner", "account", "created_date", "modified_date", "sha1", "object_id", "name", "size" ]

    def get_url(self, obj):
        frag = services.generate_refresh_fragment(obj)
        return "{}#{}".format(obj.attached_file.url, frag)

    def get_thumbnail_card_url(self, obj):
        return services.get_card_image_thumbnail_url(obj)

    def get_preview_url(self, obj):
        if obj.name.endswith(".psd"):
            return services.get_attachment_image_preview_url(obj)
        return self.get_url(obj)


class BasicAttachmentsInfoSerializerMixin(serializers.Serializer):
    """
    Assumptions:
    - The queryset has an attribute called "include_attachments" indicating if the attachments array should contain information
        about the related elements, otherwise it will be empty
    - The method attach_basic_attachments has been used to include the necessary
        json data about the attachments in the "attachments_attr" column
    """
    attachments = serializers.SerializerMethodField()

    def get_attachments(self, obj):
        include_attachments = getattr(obj, "include_attachments", False)

        if include_attachments:
            assert hasattr(obj, "attachments_attr"), "instance must have a attachments_attr attribute"

        if not include_attachments or obj.attachments_attr is None:
            return []

        for at in obj.attachments_attr:
            at["thumbnail_card_url"] = get_thumbnail_url(at["attached_file"], settings.THN_ATTACHMENT_CARD)

        return obj.attachments_attr
