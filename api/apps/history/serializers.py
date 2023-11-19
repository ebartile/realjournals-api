from rest_framework import serializers
from apps.users.services import get_user_photo_url
from .models import HistoryEntry

class HistoryEntrySerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()

    class Meta:
        model = HistoryEntry
        fields = ("id", "created_at", "user", "type", "key", "diff", "snapshot", "values", "values_diff", "comment", "comment_html", "delete_comment_date", "delete_comment_user", "edit_comment_date", "is_hidden", "is_snapshot")

    def get_user(self, entry):
        user = {"pk": None, "username": None, "name": None, "photo": None, "is_active": False}
        user.update(entry.user)
        user["photo"] = get_user_photo_url(entry.owner)

        if entry.owner:
            user["is_active"] = entry.owner.is_active

            if entry.owner.is_active or entry.owner.is_system:
                user["name"] = entry.owner.get_full_name()
                user["username"] = entry.owner.username

        return user
