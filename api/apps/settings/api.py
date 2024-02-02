import json
from django.db.models import Q
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, IsAdminUser
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet, ViewSet
from rest_framework import status
from apps.utils.exceptions import WrongArguments, PermissionDenied
from apps.accounts.permissions import HasAccountPerm
from apps.accounts.models import Account
from django.utils.translation import gettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from django.shortcuts import get_object_or_404

from . import models
from . import serializers

class TerminalPageViewSet(ReadOnlyModelViewSet):
    queryset = models.TerminalPageModule.objects.all()
    serializer_class = serializers.TerminalPageModuleSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['page']

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(account=self.kwargs['id'], status=True)

    def get_serializer(self, *args, **kwargs):
        if self.action == 'create':
            self.serializer_class = serializers.TerminalPageEditSerializer
        return super().get_serializer(*args, **kwargs)

    def create(self, request, **kwargs):
        serializer = serializers.TerminalPageEditSerializer(data=request.data)
        
        if serializer.is_valid():
            page = serializer.data.get('page')
            dimensions_data = serializer.data.get('dimensions', {})
            account = get_object_or_404(Account, id=self.kwargs['id'])
            order = 0
            for module_name, module_dimensions in dimensions_data.items():
                terminal_page_module, created = models.TerminalPageModule.objects.update_or_create(account=account, page=page, module=module_name)
                terminal_page_module.order = order
                terminal_page_module.save()
                order = order + 1
                for dimension in module_dimensions:
                    try:
                        terminal_dimensions, created = models.TerminalDimensions.objects.update_or_create(
                            module=terminal_page_module,
                            breakpoint=dimension['breakpoint'])
                        terminal_dimensions.w=dimension['w']
                        terminal_dimensions.h=dimension['h']
                        terminal_dimensions.x=dimension['x']
                        terminal_dimensions.y=dimension['y']
                        terminal_dimensions.isResizable=dimension.get('isResizable', False)
                        terminal_dimensions.moved=dimension.get('moved', False)
                        terminal_dimensions.static=dimension.get('static', False)
                        terminal_dimensions.save()
                    except IntegrityError:
                        raise serializers.ValidationError(f"Duplicate dimensions found for module '{module_name}'.")
                    
            return Response(status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AdminPageViewSet(ReadOnlyModelViewSet):
    queryset = models.AdminPageModule.objects.all()
    serializer_class = serializers.AdminPageModuleSerializer  # Assuming you have a separate serializer for AdminPageModule
    permission_classes = (IsAdminUser,)
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['page']

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(user=self.kwargs['id'], status=True)

    def get_serializer(self, *args, **kwargs):
        if self.action == 'create':
            self.serializer_class = serializers.AdminPageEditSerializer
        return super().get_serializer(*args, **kwargs)

    def create(self, request, **kwargs):
        serializer = serializers.AdminPageEditSerializer(data=request.data)
        
        if serializer.is_valid():
            page = serializer.data.get('page')
            dimensions_data = serializer.data.get('dimensions', {})
            order = 0
            for module_name, module_dimensions in dimensions_data.items():
                admin_page_module, created = models.AdminPageModule.objects.update_or_create(user=request.user, page=page, module=module_name)
                admin_page_module.order = order
                admin_page_module.save()
                order = order + 1
                for dimension in module_dimensions:
                    try:
                        admin_dimensions, created = models.AdminDimensions.objects.update_or_create(
                            module=admin_page_module,
                            breakpoint=dimension['breakpoint'])
                        admin_dimensions.w=dimension['w']
                        admin_dimensions.h=dimension['h']
                        admin_dimensions.x=dimension['x']
                        admin_dimensions.y=dimension['y']
                        admin_dimensions.isResizable=dimension.get('isResizable', False)
                        admin_dimensions.moved=dimension.get('moved', False)
                        admin_dimensions.static=dimension.get('static', False)
                        admin_dimensions.save()
                    except IntegrityError:
                        raise serializers.ValidationError(f"Duplicate dimensions found for module '{module_name}'.")
                    
            return Response(status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        

class ThemeSettingsViewSet(ViewSet):
    queryset = models.ThemeSettings.objects.all()
    serializer_class = serializers.ThemeSettingsSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_object(self):
        return self.queryset.first()  # Use first() to get a single object

    def list(self, request, **kwargs):
        instance = self.get_object()
        serializer = self.serializer_class(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request, **kwargs):
        instance = self.get_object()
        serializer = self.serializer_class(instance, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
