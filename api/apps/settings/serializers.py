from jsonschema import validate
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from .models import  TerminalPageModule, ThemeSettings, TerminalDimensions, AdminPageModule, AdminDimensions
from apps.accounts.services import is_account_admin, user_has_perm
from jsonschema import validate

class ThemeSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ThemeSettings
        fields = '__all__'

class TerminalDimensionsSerializer(serializers.ModelSerializer):

    class Meta:
        model = TerminalDimensions
        exclude = ('module', )

class AdminDimensionsSerializer(serializers.ModelSerializer):

    class Meta:
        model = AdminDimensions
        exclude = ('module', )

class TerminalPageEditSerializer(serializers.ModelSerializer):
    dimensions = serializers.JSONField()

    class Meta:
        model = TerminalPageModule
        fields = ("page", "dimensions",)

    def validate_dimensions(self, data):
        for module, module_dimensions in data.items():
            if not isinstance(module_dimensions, list):
                raise serializers.ValidationError(f"Invalid dimensions for module '{module}': must be a list.")

            for dimension in module_dimensions:
                if not isinstance(dimension, dict):
                    raise serializers.ValidationError(f"Invalid dimension in module '{module}': must be a dictionary.")

                required_keys = {'breakpoint', 'w', 'h', 'isResizable', 'x', 'y'}
                if not required_keys.issubset(dimension.keys()):
                    raise serializers.ValidationError(f"Missing or incorrect keys in dimension for module '{module}': {required_keys}")

                if not isinstance(dimension['w'], int) or not isinstance(dimension['h'], int):
                    raise serializers.ValidationError(f"Invalid data types in dimension for module '{module}': 'w', 'h' must be integers.")

                # Check the existence of keys before validating their types
                if 'isResizable' in dimension and not isinstance(dimension['isResizable'], bool):
                    raise serializers.ValidationError(f"Invalid data type for 'isResizable' in dimension for module '{module}': must be a boolean.")

                if 'moved' in dimension and not isinstance(dimension['moved'], bool):
                    raise serializers.ValidationError(f"Invalid data type for 'moved' in dimension for module '{module}': must be a boolean.")

                if 'static' in dimension and not isinstance(dimension['static'], bool):
                    raise serializers.ValidationError(f"Invalid data type for 'static' in dimension for module '{module}': must be a boolean.")

        return data

class AdminPageEditSerializer(serializers.ModelSerializer):
    dimensions = serializers.JSONField()

    class Meta:
        model = AdminPageModule
        fields = ("page", "dimensions",)

    def validate_dimensions(self, data):
        for module, module_dimensions in data.items():
            if not isinstance(module_dimensions, list):
                raise serializers.ValidationError(f"Invalid dimensions for module '{module}': must be a list.")

            for dimension in module_dimensions:
                if not isinstance(dimension, dict):
                    raise serializers.ValidationError(f"Invalid dimension in module '{module}': must be a dictionary.")

                required_keys = {'breakpoint', 'w', 'h', 'isResizable', 'x', 'y'}
                if not required_keys.issubset(dimension.keys()):
                    raise serializers.ValidationError(f"Missing or incorrect keys in dimension for module '{module}': {required_keys}")

                if not isinstance(dimension['w'], int) or not isinstance(dimension['h'], int):
                    raise serializers.ValidationError(f"Invalid data types in dimension for module '{module}': 'w', 'h' must be integers.")

                # Check the existence of keys before validating their types
                if 'isResizable' in dimension and not isinstance(dimension['isResizable'], bool):
                    raise serializers.ValidationError(f"Invalid data type for 'isResizable' in dimension for module '{module}': must be a boolean.")

                if 'moved' in dimension and not isinstance(dimension['moved'], bool):
                    raise serializers.ValidationError(f"Invalid data type for 'moved' in dimension for module '{module}': must be a boolean.")

                if 'static' in dimension and not isinstance(dimension['static'], bool):
                    raise serializers.ValidationError(f"Invalid data type for 'static' in dimension for module '{module}': must be a boolean.")

        return data

class TerminalPageModuleSerializer(serializers.ModelSerializer):
    dimensions = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    class Meta:
        model = TerminalPageModule
        fields = ("page", "status", "order", "created_at", "name", "dimensions")

    def get_dimensions(self, obj):
        return TerminalDimensionsSerializer(obj.dimensions, many=True).data

    def get_name(self, obj):
        return obj.module.name

    def get_status(self, obj):
        if not obj.module.is_active:
            return obj.module.is_active
        return obj.status

class AdminPageModuleSerializer(serializers.ModelSerializer):
    dimensions = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    class Meta:
        model = AdminPageModule
        fields = ("page", "status", "order", "created_at", "name", "dimensions")

    def get_dimensions(self, obj):
        return AdminDimensionsSerializer(obj.dimensions, many=True).data

    def get_name(self, obj):
        return obj.module.name

    def get_status(self, obj):
        if not obj.module.is_active:
            return obj.module.is_active
        return obj.status
