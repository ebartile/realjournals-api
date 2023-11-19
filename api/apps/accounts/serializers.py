from rest_framework import serializers
from apps.users.serializers import UserBasicInfoSerializer
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from . import models
from .services import *

class UploadDataSerializer(serializers.ModelSerializer):
    attachment = serializers.IntegerField(required=True)

    class Meta:
        model = models.Account
        fields = ("attachment", "broker", "timezone",)

class BrokerSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Broker
        fields = "__all__"

class AccountCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Account
        fields = ["name", "description", "is_private",]

class AccountSerializer(serializers.ModelSerializer):
    owner = serializers.SerializerMethodField()
    members = serializers.SerializerMethodField()
    my_permissions = serializers.SerializerMethodField()
    i_am_owner = serializers.SerializerMethodField()
    i_am_admin = serializers.SerializerMethodField()
    i_am_member = serializers.SerializerMethodField()
    logo_small_url = serializers.SerializerMethodField()    

    class Meta:
        model = models.Account
        read_only_fields = ["id", "slug", "created_date", "modified_date", "public_permissions", "is_admin", "is_featured", "blocked_code", "logo"]
        fields = ["id", "name", "slug", "description", "broker", "logo", "timezone", "created_date", "modified_date", "has_be_configured", "owner", "members", "is_private", "public_permissions", "is_admin", "is_featured", "blocked_code", "my_permissions", "i_am_owner", "i_am_member", "i_am_admin", "logo_small_url",]


    def get_owner(self, obj):
        return UserBasicInfoSerializer(obj.owner).data

    def get_members(self, obj):
        assert hasattr(obj, "members_attr"), "instance must have a members_attr attribute"
        if obj.members_attr is None:
            return []

        return [m.get("id") for m in obj.members_attr if m["id"] is not None]

    def get_i_am_member(self, obj):
        assert hasattr(obj, "members_attr"), "instance must have a members_attr attribute"
        if obj.members_attr is None:
            return False

        if "request" in self.context:
            user = self.context["request"].user
            user_ids = [m.get("id") for m in obj.members_attr if m["id"] is not None]
            if not user.is_anonymous and user.id in user_ids:
                return True

        return False

    def get_my_permissions(self, obj):
        if "request" in self.context:
            user = self.context["request"].user
            return calculate_permissions(is_authenticated=user.is_authenticated,
                                         is_superuser=user.is_superuser,
                                         is_member=self.get_i_am_member(obj),
                                         is_admin=self.get_i_am_admin(obj),
                                         role_permissions=obj.my_role_permissions_attr,
                                         public_permissions=obj.public_permissions)
        return []

    def get_i_am_owner(self, obj):
        if "request" in self.context:
            return is_account_owner(self.context["request"].user, obj)
        return False

    def get_i_am_admin(self, obj):
        if "request" in self.context:
            return is_account_admin(self.context["request"].user, obj)
        return False

    def get_logo_small_url(self, obj):
        return get_logo_small_thumbnail_url(obj)


class AccountDetailSerializer(AccountSerializer):
    total_memberships = serializers.SerializerMethodField()
    is_private_extra_info = serializers.SerializerMethodField()
    max_memberships = serializers.SerializerMethodField()
    is_out_of_owner_limits = serializers.SerializerMethodField()

    class Meta:        
        model = models.Account
        read_only_fields = AccountSerializer.Meta.read_only_fields
        fields = AccountSerializer.Meta.fields + ["total_memberships", "is_private_extra_info", "max_memberships", "is_out_of_owner_limits",]


    def to_representation(self, instance):
        for attr in ["roles_attr",]:

            assert hasattr(instance, attr), "instance must have a {} attribute".format(attr)
            val = getattr(instance, attr)
            if val is None:
                continue

            for elem in val:
                elem["name"] = _(elem["name"])

        representation = super().to_representation(instance)
        admin_fields = [
            "is_private_extra_info", "max_memberships",
        ]

        is_admin_user = False
        if "request" in self.context:
            user = self.context["request"].user
            is_admin_user = is_account_admin(user, instance)

        if not is_admin_user:
            for admin_field in admin_fields:
                del(representation[admin_field])

        return representation

    def get_total_memberships(self, obj):
        if obj.members_attr is None:
            return 0

        return len(obj.members_attr)

    def get_is_private_extra_info(self, obj):
        assert hasattr(obj, "private_accounts_same_owner_attr"), ("instance must have a private_accounts_same_"
                                                                  "owner_attr attribute")
        assert hasattr(obj, "public_accounts_same_owner_attr"), ("instance must have a public_accounts_same"
                                                                 "_owner_attr attribute")
        return check_if_account_privacy_can_be_changed(
            obj,
            current_memberships=self.get_total_memberships(obj),
            current_private_accounts=obj.private_accounts_same_owner_attr,
            current_public_accounts=obj.public_accounts_same_owner_attr
        )

    def get_max_memberships(self, obj):
        return get_max_memberships_for_account(obj)


    def get_is_out_of_owner_limits(self, obj):
        assert hasattr(obj, "private_accounts_same_owner_attr"), ("instance must have a private_accounts_same"
                                                                  "_owner_attr attribute")
        assert hasattr(obj, "public_accounts_same_owner_attr"), ("instance must have a public_accounts_same_"
                                                                 "owner_attr attribute")
        return check_if_account_is_out_of_owner_limits(
            obj,
            current_memberships=self.get_total_memberships(obj),
            current_private_accounts=obj.private_accounts_same_owner_attr,
            current_public_accounts=obj.public_accounts_same_owner_attr
        )

    def get_is_private_extra_info(self, obj):
        assert hasattr(obj, "private_accounts_same_owner_attr"), ("instance must have a private_accounts_same_"
                                                                  "owner_attr attribute")
        assert hasattr(obj, "public_accounts_same_owner_attr"), ("instance must have a public_accounts_same"
                                                                 "_owner_attr attribute")
        return check_if_account_privacy_can_be_changed(
            obj,
            current_memberships=self.get_total_memberships(obj),
            current_private_accounts=obj.private_accounts_same_owner_attr,
            current_public_accounts=obj.public_accounts_same_owner_attr
        )

class AccountExistsSerializer:
    def validate_account_id(self, value):
        if not models.Account.objects.filter(pk=value).exists():
            msg = _("There's no account with that id")
            raise ValidationError(msg)
        return value

class UpdateAccountOrderBulkSerializer(AccountExistsSerializer, serializers.Serializer):
    account_id = serializers.IntegerField()
    order = serializers.IntegerField()

    def validate(self, data):
        data = super().validate(data)
        return data
