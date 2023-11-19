from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import status
from rest_framework.viewsets import ReadOnlyModelViewSet
from apps.utils.mdrender.service import render as mdrender
from apps.notifications import services as notifications_services
from apps.notifications.apps import signal_mentions
from . import serializers
from . import services
from . import permissions
from apps.accounts.permissions import HasAccountPerm


class HistoryViewSet(ReadOnlyModelViewSet):
    serializer_class = serializers.HistoryEntrySerializer
    content_type = None

    def get_content_type(self):
        app_name, model = self.content_type.split(".", 1)
        return ContentType.objects.get_by_natural_key(app_name, model)

    def get_queryset(self):
        ct = self.get_content_type()
        model_cls = ct.model_class()

        qs = model_cls.objects.all()
        filtered_qs = self.filter_queryset(qs)
        return filtered_qs

    def response_for_queryset(self, queryset):
        # Switch between paginated or standard style responses
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_pagination_serializer(page)
        else:
            serializer = self.get_serializer(queryset, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def _get_new_mentions(self, obj: object, old_comment: str, new_comment: str):
        old_mentions = notifications_services.get_mentions(obj.account, old_comment)
        submitted_mentions = notifications_services.get_mentions(obj, new_comment)
        return list(set(submitted_mentions) - set(old_mentions))

    @action(detail=True, methods=['GET'])
    def comment_versions(self, request, pk):
        obj = self.get_object()
        history_entry_id = request.query_params.get('id', None)
        history_entry = services.get_history_queryset_by_model_instance(obj).filter(id=history_entry_id).first()
        if history_entry is None:
            return response.NotFound()

        self.check_permissions(request, 'comment_versions', history_entry)

        if history_entry is None:
            return response.NotFound()

        history_entry.attach_user_info_to_comment_versions()
        return Response(history_entry.comment_versions, status=status.HTTP_200_OK)

    @action(detail=True, methods=['POST'])
    def edit_comment(self, request, pk):
        obj = self.get_object()
        history_entry_id = request.query_params.get('id', None)
        history_entry = services.get_history_queryset_by_model_instance(obj).filter(id=history_entry_id).first()
        if history_entry is None:
            return response.NotFound()

        obj = services.get_instance_from_key(history_entry.key)
        comment = request.DATA.get("comment", None)

        self.check_permissions(request, 'edit_comment', history_entry)

        if history_entry is None:
            return response.NotFound()

        if comment is None:
            return response.BadRequest({"error": _("comment is required")})

        if history_entry.delete_comment_date or history_entry.delete_comment_user:
            return response.BadRequest({"error": _("deleted comments can't be edited")})

        # comment_versions can be None if there are no historic versions of the comment
        comment_versions = history_entry.comment_versions or []
        comment_versions.append({
            "date": history_entry.created_at,
            "comment": history_entry.comment,
            "comment_html": history_entry.comment_html,
            "user": {
                "id": request.user.pk,
            }
        })

        new_mentions = self._get_new_mentions(obj, history_entry.comment, comment)

        history_entry.edit_comment_date = timezone.now()
        history_entry.comment = comment
        history_entry.comment_html = mdrender(obj.account, comment)
        history_entry.comment_versions = comment_versions
        history_entry.save()

        if new_mentions:
            signal_mentions.send(sender=self.__class__,
                                 user=self.request.user,
                                 obj=obj,
                                 mentions=new_mentions)

        return Response(status=status.HTTP_200_OK)

    @action(detail=True, methods=['POST'])
    def delete_comment(self, request, pk):
        obj = self.get_object()
        history_entry_id = request.query_params.get('id', None)
        history_entry = services.get_history_queryset_by_model_instance(obj).filter(id=history_entry_id).first()
        if history_entry is None:
            return response.NotFound()

        self.check_permissions(request, 'delete_comment', history_entry)

        if history_entry is None:
            return response.NotFound()

        if history_entry.delete_comment_date or history_entry.delete_comment_user:
            return response.BadRequest({"error": _("Comment already deleted")})

        history_entry.delete_comment_date = timezone.now()
        history_entry.delete_comment_user = {"pk": request.user.pk, "name": request.user.get_full_name()}
        history_entry.save()
        return Response(status=status.HTTP_200_OK)

    @action(detail=True, methods=['POST'])
    def undelete_comment(self, request, pk):
        obj = self.get_object()
        history_entry_id = request.query_params.get('id', None)
        history_entry = services.get_history_queryset_by_model_instance(obj).filter(id=history_entry_id).first()
        if history_entry is None:
            return response.NotFound()

        self.check_permissions(request, 'undelete_comment', history_entry)

        if history_entry is None:
            return response.NotFound()

        if not history_entry.delete_comment_date and not history_entry.delete_comment_user:
            return response.BadRequest({"error": _("Comment not deleted")})

        history_entry.delete_comment_date = None
        history_entry.delete_comment_user = None
        history_entry.save()
        return Response(status=status.HTTP_200_OK)

    # Just for restframework! Because it raises
    # 404 on main api root if this method not exists.
    def list(self, request):
        return response.NotFound()

    def retrieve(self, request, pk):
        obj = self.get_object()
        self.check_permissions(request, "retrieve", obj)
        qs = services.get_history_queryset_by_model_instance(obj)

        history_type = self.request.GET.get('type')
        if history_type == 'activity':
            qs = qs.filter(diff__isnull=False, comment__exact='').exclude(diff__exact='')

        if history_type == 'comment':
            qs = qs.exclude(comment__exact='')

        qs = qs.order_by("-created_at")
        qs = services.prefetch_owners_in_history_queryset(qs)

        if self.request.GET.get(self.page_kwarg):
            page = self.paginate_queryset(qs)
            serializer = self.get_pagination_serializer(page)
            return Response(serializer.data, status=status.HTTP_200_OK)

        return self.response_for_queryset(qs)


class JournalHistory(HistoryViewSet):
    content_type = "journals.journal"
    permission_classes = (permissions.IsCommentAccountAdmin() | permissions.IsCommentOwner())

    def get_permissions(self):
        if self.action == "retrieve":
            self.permission_classes = (HasAccountPerm("view_account"),)

        return super().get_permissions()
