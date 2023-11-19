from rest_framework import serializers
from django.core.exceptions import ValidationError

class ResolverSerializer(serializers.Serializer):
    account = serializers.CharField(max_length=512, required=True)
    journal = serializers.IntegerField(required=False)
    ref = serializers.CharField(max_length=512, required=False)

    def validate(self, attrs):
        if "ref" in attrs:
            if "journal" in attrs:
                raise ValidationError("'journal' param is incompatible with 'ref' in the same request")

        return attrs
