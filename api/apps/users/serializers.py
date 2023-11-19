from django.contrib.auth import password_validation
from apps.utils.exceptions import RequestValidationError
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from django.utils import timezone
from .services import get_user_photo_url, get_user_big_photo_url
from .models import User, Role
from datetime import datetime

class UserJoinStatsSerializer(serializers.Serializer):
    total = serializers.IntegerField()
    date = serializers.DateField()
    
            
class UserSerializer(serializers.ModelSerializer):
    is_profile_complete = serializers.SerializerMethodField()
    has_account = serializers.SerializerMethodField()
    account_has_be_configured = serializers.SerializerMethodField()
    full_name_display = serializers.SerializerMethodField()
    big_photo = serializers.SerializerMethodField()
    country_name = serializers.SerializerMethodField()
    currency_name = serializers.SerializerMethodField()
    continent_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        exclude = ['password', 'email_verified_at', 'token', 'email_token', 'new_email',]
        read_only_fields = ['id', 'uuid', 'username', 'email', 'is_active', 'is_superuser', 'is_staff', 'photo', 'last_login', 'last_seen', 'email_verified_at', 'date_joined', 'updated_at', 'has_account', 'account_has_be_configured', 'is_profile_complete','two_factor_enabled', 'verified_email', 'is_system', 'max_private_accounts', 'max_public_accounts', 'max_memberships_private_accounts', 'max_memberships_public_accounts', 'registered_by', 'location',]

    def get_currency_name(self, obj):
        return obj.get_currency_name()

    def get_country_name(self, obj):
        return obj.get_country_name()

    def get_continent_name(self, obj):
        return obj.get_continent_name()

    def get_has_account(self, obj):
        if obj.owned_accounts.all().count() > 0:
            return True
        return False 

    def get_account_has_be_configured(self, obj):
        if obj.owned_accounts.all().count() > 0:
            if obj.owned_accounts.filter(has_be_configured=True).count() > 0:
                return True
        return False 

    def get_is_profile_complete(self, obj):
        if obj.first_name and obj.last_name and obj.country and obj.date_of_birth:
            return True            
        return False 

    def get_full_name_display(self, obj):
        return obj.get_full_name() if obj else ""

    def get_photo(self, user):
        return get_user_photo_url(user)
    
    def get_big_photo(self, user):
        return get_user_big_photo_url(user)

class UserAdminSerializer(UserSerializer):
    pass
    # TODO:


class BaseRegisterSerializer(serializers.ModelSerializer):
    accepted_terms = serializers.BooleanField(default=True)

    class Meta:        
        model = User
        fields = ['first_name', 'last_name', 'email', 'password', 'accepted_terms']

    def validate_accepted_terms(self, value):
        """
        Custom validation for the accepted_terms field.
        """
        if not value:
            raise RequestValidationError(_(f"You must accept our terms of service and privacy policy"))
        return value

class PublicRegisterSerializer(BaseRegisterSerializer):
    pass

class PrivateRegisterSerializer(serializers.ModelSerializer):
    class Meta:        
        model = User
        fields = ['first_name', 'last_name', 'email',]

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=255)
    password = serializers.CharField()
    otp_token = serializers.CharField(required=False)
    invitation_token = serializers.CharField(max_length=255, required=False)


class UserBasicInfoSerializer(serializers.ModelSerializer):
    full_name_display = serializers.SerializerMethodField()
    big_photo = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "email", "username", "full_name_display", "photo", "big_photo", "is_active")

    def get_full_name_display(self, obj):
        return obj.get_full_name() if obj else ""

    def get_photo(self, user):
        return get_user_photo_url(user)
    
    def get_big_photo(self, user):
        return get_user_big_photo_url(user)

class RecoverySerializer(serializers.Serializer):
    token = serializers.CharField(required=True, max_length=200)
    password = serializers.CharField(required=True, min_length=6)

class ChangeEmailSerializer(serializers.Serializer):
    email_token = serializers.CharField(max_length=200)

class CancelAccountSerializer(serializers.Serializer):
    cancel_token = serializers.CharField(max_length=200)


class RoleSerializer(serializers.ModelSerializer):
    members_count = serializers.SerializerMethodField()

    class Meta:
        model = Role
        fields = ("id", "name", "slug", "account", "order", "computable", "permissions", "members_count")
        read_only_fields = ("id", "slug", )
        i18n_fields = ("name",)

    def get_members_count(self, obj):
        return obj.memberships.count()
