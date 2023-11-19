from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers
from apps.users.models import User
from apps.users.services import get_user_photo_url, get_user_big_photo_url
from . import models


class NotifyPolicySerializer(serializers.ModelSerializer):
    account_name = serializers.SerializerMethodField()

    class Meta:
        model = models.NotifyPolicy
        fields = ('id', 'account', 'account_name', 'notify_level',
                  'live_notify_level', 'web_notify_level')
        read_only_fields = ("id", "account",)

    def get_account_name(self, obj):
        return obj.account.name


class WatcherSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(required=False)

    class Meta:
        model = User
        fields = ('id', 'username', 'full_name')

    def get_full_name(self, obj):
        return obj.get_full_name()


class WebNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.WebNotification
        fields = ('id', 'event_type', 'user', 'data', 'created', 'read')


class AccountSerializer(serializers.Serializer):
    id = serializers.CharField()
    slug = serializers.CharField()
    name = serializers.CharField()


class ObjectSerializer(serializers.Serializer):
    id = serializers.CharField()
    ref = serializers.SerializerMethodField()
    subject = serializers.SerializerMethodField()
    content_type = serializers.SerializerMethodField()

    def get_ref(self, obj):
        return obj.ref if hasattr(obj, 'ref') else None

    def get_subject(self, obj):
        return obj.subject if hasattr(obj, 'subject') else None

    def get_content_type(self, obj):
        content_type = ContentType.objects.get_for_model(obj)
        return content_type.model if content_type else None


class UserSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.SerializerMethodField()
    photo = serializers.SerializerMethodField()
    big_photo = serializers.SerializerMethodField()
    gravatar_id = serializers.SerializerMethodField()
    username = serializers.CharField()
    is_profile_visible = serializers.SerializerMethodField()
    date_joined = serializers.DateTimeField()

    def get_name(self, obj):
        return obj.get_full_name()

    def get_photo(self, obj):
        return get_user_photo_url(obj)

    def get_big_photo(self, obj):
        return get_user_big_photo_url(obj)

    def get_is_profile_visible(self, obj):
        return obj.is_active and not obj.is_system


class NotificationDataSerializer(serializers.Serializer):
    account = AccountSerializer()
    user = UserSerializer()


class ObjectNotificationSerializer(NotificationDataSerializer):
    obj = ObjectSerializer()
