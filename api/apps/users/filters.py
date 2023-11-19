import logging
from apps.accounts.filters import FilterBackend
from apps.utils.exceptions import BadRequest
from django.utils.translation import gettext_lazy as _
from django.apps import apps
from django.db.models import Q
import django_filters
from .models import User

logger = logging.getLogger(__name__)

#####################################################################
# Permissions filters
#####################################################################

class UserFilter(django_filters.FilterSet):
    date_joined__year = django_filters.NumberFilter(field_name='date_joined', lookup_expr='year')
    date_joined__month = django_filters.NumberFilter(field_name='date_joined', lookup_expr='month')

    class Meta:
        model = User
        fields = []

class PermissionBasedFilterBackend(FilterBackend):
    permission = None
    account_query_param = "account"

    def filter_queryset(self, request, queryset, view):
        account_id = None
        if (hasattr(view, "filter_fields") and "account" in view.filter_fields and
                "account" in request.query_params):
            try:
                account_id = int(request.query_params["account"])
            except:
                logger.error("Filtering account diferent value than an integer: {}".format(
                    request.query_params["account"]
                ))
                raise BadRequest(_("'account' must be an integer value."))

        qs = queryset

        if request.user.is_authenticated and request.user.is_superuser:
            qs = qs
        elif request.user.is_authenticated:
            membership_model = apps.get_model('accounts', 'Membership')
            memberships_qs = membership_model.objects.filter(user=request.user)
            if account_id:
                memberships_qs = memberships_qs.filter(account_id=account_id)
            memberships_qs = memberships_qs.filter(
                Q(role__permissions__contains=[self.permission]) |
                Q(is_admin=True))

            accounts_list = [membership.account_id for membership in memberships_qs]

            qs = qs.filter(Q(**{f"{self.account_query_param}_id__in": accounts_list}) |
                           Q(**{f"{self.account_query_param}__public_permissions__contains": [self.permission]}))
        else:
            qs = qs.filter(**{f"{self.account_query_param}__anon_permissions__contains": [self.permission]})

        return super().filter_queryset(request, qs, view)


class CanViewAccountFilterBackend(PermissionBasedFilterBackend):
    permission = "view_account"
