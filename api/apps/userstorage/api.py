from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils.translation import gettext_lazy as _
from . import models, serializers, filters
from rest_framework import exceptions as exc

class StorageEntriesViewSet(viewsets.ModelViewSet):
    model = models.StorageEntry
    filter_backends = (filters.StorageEntriesFilterBackend,)
    serializer_class = serializers.StorageEntrySerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "key"

    def get_queryset(self):
        if self.request.user.is_anonymous:
            return self.model.objects.none()
        return self.request.user.storage_entries.all()

    def perform_create(self, serializer):
        key = serializer.validated_data.get("key")
        if self.request.user.storage_entries.filter(key=key).exists():
            raise exc.ValidationError(
                {"key": [_("Key '{}' already exists.").format(key)]}
            )
        serializer.save(owner=self.request.user)

    def perform_update(self, serializer):
        key = serializer.validated_data.get("key")
        if self.request.user.storage_entries.filter(key=key).exclude(pk=self.get_object().pk).exists():
            raise exc.ValidationError(
                {"key": [_("Key '{}' already exists.").format(key)]}
            )
        serializer.save()
