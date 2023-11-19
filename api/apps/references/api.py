from django.apps import apps

from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from apps.accounts.services import user_has_perm
from rest_framework import viewsets
from .serializers import ResolverSerializer
from apps.accounts.permissions import HasAccountPerm
from apps.utils.exceptions import BadRequest


class ResolverViewSet(viewsets.ViewSet):
    permission_classes = (HasAccountPerm("view_account"),)

    def list(self, request, **kwargs):
        serializer = ResolverSerializer(data=request.query_params)
        if not serializer.is_valid():
            raise BadRequest(serializer.errors)

        data = serializer.data

        account_model = apps.get_model("accounts", "Account")
        account = get_object_or_404(account_model, slug=data["account"])

        result = {"account": account.pk}

        if data["journal"] and user_has_perm(request.user, "view_journal", account):
            result["journal"] = get_object_or_404(account.issues.all(),
                                                ref=data["issue"]).pk

        if data["ref"]:
            ref_found = False  # No need to continue once one ref is found
            try:
                value = int(data["ref"])

                if ref_found is False and user_has_perm(request.user, "view_journal", account):
                    journal = account.journals.filter(ref=value).first()
                    if journal:
                        result["journal"] = journal.pk
            except:
                value = data["ref"]

        return Response(result, status=status.HTTP_200_OK)
