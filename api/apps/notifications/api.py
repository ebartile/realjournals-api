from django.db.models import Q
from django.utils import timezone
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from django.shortcuts import get_object_or_404

from .choices import NotifyLevel
from apps.accounts.models import Account
from . import serializers
from . import models
from . import services
from . import permissions


class NotifyPolicyViewSet(ModelViewSet):
    serializer_class = serializers.NotifyPolicySerializer
    permission_classes = (IsAuthenticated,)

    def _build_needed_notify_policies(self):
        accounts = Account.objects.filter(
            Q(owner=self.request.user) |
            Q(memberships__user=self.request.user)
        ).distinct()

        for account in accounts:
            services.create_notify_policy_if_not_exists(account, self.request.user, NotifyLevel.all)

    def get_queryset(self):
        if self.request.user.is_anonymous:
            return models.NotifyPolicy.objects.none()

        self._build_needed_notify_policies()

        return models.NotifyPolicy.objects.filter(user=self.request.user).filter(
            Q(account__owner=self.request.user) | Q(account__memberships__user=self.request.user)
        ).distinct()


class WebNotificationsViewSet(GenericViewSet):
    serializer_class = serializers.WebNotificationSerializer
    resource_model = models.WebNotification
    permission_classes = (permissions.WebNotificationsPermission,)

    def list(self, request):
        if self.request.user.is_anonymous:
            return Response(status=status.HTTP_200_OK)

        queryset = models.WebNotification.objects\
            .filter(user=self.request.user)

        if request.GET.get("only_unread", False):
            queryset = queryset.filter(read__isnull=True)

        queryset = queryset.order_by('-read', '-created')

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.serializer_class(page, many=True)
            return Response({
                "objects": serializer.data,
                "total": queryset.count()
            }, status=status.HTTP_200_OK)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, *args, **kwargs):
        resource_id = kwargs.get("resource_id", None)
        resource = get_object_or_404(self.resource_model, pk=resource_id)
        resource.read = timezone.now()
        resource.save()

        return Response({}, status=status.HTTP_200_OK)

    def post(self, request):
        models.WebNotification.objects.filter(user=self.request.user)\
            .update(read=timezone.now())

        return Response(status=status.HTTP_200_OK)
