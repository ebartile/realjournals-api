from django.core.exceptions import ObjectDoesNotExist

from rest_framework.response import Response
from rest_framework import viewsets
from rest_framework import status
from django.shortcuts import get_object_or_404
from rest_framework.decorators import action

from apps.likes import serializers
from apps.likes import services


class LikedResourceMixin:
    """
    NOTE:the classes using this mixing must have a method:
    def pre_conditions_on_save(self, obj)
    """
    @action(detail=True, methods=['POST'])
    def like(self, request, pk=None):
        obj = self.get_object()
        services.add_like(obj, user=request.user)
        return Response(status=status.HTTP_200_OK)

    @action(detail=True, methods=['POST'])
    def unlike(self, request, pk=None):
        obj = self.get_object()
        services.remove_like(obj, user=request.user)
        return Response(status=status.HTTP_200_OK)


class FansViewSetMixin:
    # Is a ModelListViewSet with two required params: permission_classes and resource_model
    serializer_class = serializers.FanSerializer
    permission_classes = None
    resource_model = None

    def retrieve(self, request, *args, **kwargs):
        pk = kwargs.get("pk", None)
        resource_id = kwargs.get("resource_id", None)
        resource = get_object_or_404(self.resource_model, pk=resource_id)

        try:
            self.object = services.get_fans(resource).get(pk=pk)
        except ObjectDoesNotExist: # or User.DoesNotExist
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(self.object)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def list(self, request, *args, **kwargs):
        resource_id = kwargs.get("resource_id", None)
        resource = get_object_or_404(self.resource_model, pk=resource_id)
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        resource = self.resource_model.objects.get(pk=self.kwargs.get("resource_id"))
        return services.get_fans(resource)
