import os.path as path
import mimetypes
mimetypes.init()

from rest_framework.permissions import IsAuthenticated
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from rest_framework.viewsets import ModelViewSet
from rest_framework import status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from apps.utils.exceptions import Blocked, WrongArguments, NotSupported
from apps.accounts.permissions import HasAccountPerm
from rest_framework.permissions import AllowAny
from apps.accounts.models import Account
from apps.notifications.mixins import WatchedResourceMixin
from apps.history.mixins import HistoryResourceMixin

from . import permissions
from . import serializers
from . import models
from . import filters


class BaseAttachmentViewSet(HistoryResourceMixin, WatchedResourceMixin,
                            ModelViewSet):

    model = models.Attachment
    serializer_class = serializers.AttachmentSerializer
    filter_fields = ["account", "object_id"]

    content_type = None

    def pre_conditions_blocked(self, obj):
        if obj is not None and self.is_blocked(obj):
            raise Blocked(_("This account is currently blocked"))

    def perform_create(self, serializer):
        obj = get_object_or_404(Account, id=self.kwargs['id'])

        self.pre_conditions_blocked(obj)

        if self.get_content_type() is None:
            raise WrongArguments(_("Object id journal doesn't exist"))

        file = self.request.FILES.get('attached_file', None)

        obj = serializer.save(
            account = obj,
            object_id = obj.id,
            content_type = self.get_content_type(),
            owner = self.request.user,
            size = file.size,
            name = path.basename(file.name)
        )


    def perform_update(self, serializer):
        obj = get_object_or_404(Account, id=self.kwargs['id'])

        self.pre_conditions_blocked(obj)

        if self.get_content_type() is None:
            raise WrongArguments(_("Object id journal doesn't exist"))

        if obj.account_id != obj.content_object.account_id:
            raise WrongArguments(_("Account ID does not match between object and account"))
        
        return super().perform_update(serializer)


    def perform_destroy(self, instance):
        try:
            self.pre_conditions_blocked(instance)
            # self.persist_history_snapshot(instance, delete=True)
            instance.delete()
        except Blocked as e:
            raise Blocked({"detail": str(e)})
        return Response(status=status.HTTP_204_NO_CONTENT)

    def is_blocked(self, obj):
        return obj.account is not None and obj.account.blocked_code is not None

    def partial_update(self, request, *args, **kwargs):
        raise NotSupported(_("Not Supported"))

    def get_content_type(self):
        app_name, model = self.content_type.split(".", 1)
        return get_object_or_404(ContentType, app_label=app_name, model=model)


class AccountAttachmentsViewSet(BaseAttachmentViewSet):
    queryset = models.Attachment.objects.all()
    permission_classes = (IsAuthenticated(),)
    filter_backends = (filters.CanViewJournalAttachmentFilterBackend,)
    content_type = "accounts.account"
    serializer_class = serializers.AttachmentSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        qs.filter(account=self.kwargs['id'])
        return qs

    def get_permissions(self):
        if self.action == "create":
            self.permission_classes = (IsAuthenticated(), HasAccountPerm('modify_account') | (permissions.CommentAttachmentPerm() & HasAccountPerm('comment_journal')),)
        elif self.action == "list":
            self.permission_classes = (IsAuthenticated(), HasAccountPerm('modify_account'),)
        elif self.action == "retrieve":
            self.permission_classes = (IsAuthenticated(), HasAccountPerm('modify_account') | permissions.IsAttachmentOwnerPerm(),)
        elif self.action == "update" \
            or self.action == "partial_update" \
            or self.action == "destroy":
            self.permission_classes = (IsAuthenticated(), HasAccountPerm('modify_account') | permissions.IsAttachmentOwnerPerm(),)
        return self.permission_classes

    def perform_create(self, serializer):
        obj = get_object_or_404(Account, id=self.kwargs['id'])

        self.pre_conditions_blocked(obj)

        if self.get_content_type() is None:
            raise WrongArguments(_("Object id journal doesn't exist"))

        file = self.request.FILES.get('attached_file', None)

        obj = serializer.save(
            account = obj,
            object_id = obj.id,
            content_type = self.get_content_type(),
            owner = self.request.user,
            size = file.size,
            name = path.basename(file.name)
        )

class JournalAttachmentViewSet(BaseAttachmentViewSet):
    permission_classes = (IsAuthenticated,)
    filter_backends = (filters.CanViewJournalAttachmentFilterBackend,)
    content_type = "journals.journal"

    def get_permissions(self):
        if self.action == "create":
            self.permission_classes = (HasAccountPerm('modify_journal') | (permissions.CommentAttachmentPerm() & HasAccountPerm('comment_journal')))
        elif self.action == "list":
            self.permission_classes = (HasAccountPerm('view_journal'))
        elif self.action == "retrieve":
            self.permission_classes = (HasAccountPerm('view_journal') | permissions.IsAttachmentOwnerPerm())
        elif self.action == "update" \
            or self.action == "partial_update" \
            or self.action == "destroy":
            self.permission_classes = (HasAccountPerm('modify_journal') | permissions.IsAttachmentOwnerPerm())
        return super().get_permissions()
