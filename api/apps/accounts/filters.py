import logging
import django_filters
from django.db.models import Q
from django.apps import apps
from rest_framework.filters import BaseFilterBackend
from apps.utils.exceptions import BadRequest
from django.utils.translation import gettext_lazy as _
from .models import Broker

logger = logging.getLogger(__name__)


class BrokerFilter(django_filters.FilterSet):
    class Meta:
        model = Broker
        fields = {
            'supports_stocks': ['exact'],
            'supports_options': ['exact'],
            'supports_forex': ['exact'],
            'supports_futures': ['exact'],
            'supports_crypto': ['exact'],
            'supports_metatrader_4': ['exact'],
            'supports_metatrader_5': ['exact'],
            'supports_file_import': ['exact'],
            'supports_auto_sync_import': ['exact'],
        }

def get_filter_expression_can_view_accounts(user, account_id=None):
    # Filter by user permissions
    if user.is_authenticated and user.is_superuser:
        return Q()
    elif user.is_authenticated:
        # authenticated user & account member
        membership_model = apps.get_model("accounts", "Membership")
        memberships_qs = membership_model.objects.filter(user=user)
        if account_id:
            memberships_qs = memberships_qs.filter(account_id=account_id)
        memberships_qs = memberships_qs.filter(
            Q(role__permissions__contains=['view_account']) |
            Q(is_admin=True))

        accounts_list = [membership.account_id for membership in
                         memberships_qs]

        return (Q(id__in=accounts_list) |
                Q(public_permissions__contains=["view_account"]))
    else:
        # external users / anonymous
        return Q(anon_permissions__contains=["view_account"])


class QueryParamsFilterMixin(BaseFilterBackend):
    _special_values_dict = {
        'true': True,
        'false': False,
        'null': None,
    }

    def filter_queryset(self, request, queryset, view):
        query_params = {}

        if not hasattr(view, "filter_fields"):
            return queryset

        for field in view.filter_fields:
            if isinstance(field, (tuple, list)):
                param_name, field_name = field
            else:
                param_name, field_name = field, field

            if param_name in request.query_params:
                field_data = request.query_params[param_name]
                if field_data in self._special_values_dict:
                    query_params[field_name] = self._special_values_dict[field_data]
                else:
                    query_params[field_name] = field_data

        if query_params:
            try:
                queryset = queryset.filter(**query_params)
            except ValueError:
                raise BadRequest(_("Error in filter params types."))

        return queryset


class OrderByFilterMixin(QueryParamsFilterMixin):
    order_by_query_param = "order_by"

    def filter_queryset(self, request, queryset, view):
        queryset = super().filter_queryset(request, queryset, view)
        order_by_fields = getattr(view, "order_by_fields", None)

        raw_fieldname = request.query_params.get(self.order_by_query_param, None)
        if not raw_fieldname or not order_by_fields:
            return queryset

        if raw_fieldname.startswith("-"):
            field_name = raw_fieldname[1:]
        else:
            field_name = raw_fieldname

        if field_name not in order_by_fields:
            return queryset

        if raw_fieldname in ["owner", "-owner", "assigned_to", "-assigned_to"]:
            raw_fieldname = "{}__full_name".format(raw_fieldname)

        # We need to add a default order if raw_fieldname gives rows with the same value
        return super().filter_queryset(request, queryset.order_by(raw_fieldname, "-id"), view)


class FilterBackend(OrderByFilterMixin):
    """
    Default filter backend.
    """
    pass


class UserOrderFilterBackend(FilterBackend):
    def filter_queryset(self, request, queryset, view):
        if request.user.is_anonymous:
            return queryset

        raw_fieldname = request.query_params.get(self.order_by_query_param, None)
        if not raw_fieldname:
            return queryset

        if raw_fieldname.startswith("-"):
            field_name = raw_fieldname[1:]
        else:
            field_name = raw_fieldname

        if field_name != "user_order":
            return queryset

        model = queryset.model
        sql = """SELECT accounts_membership.user_order
                 from accounts_membership
                 WHERE
                    accounts_membership.account_id = {tbl}.id AND
                    accounts_membership.user_id = {user_id}
              """

        sql = sql.format(tbl=model._meta.db_table, user_id=request.user.id)
        queryset = queryset.extra(select={"user_order": sql})
        queryset = queryset.order_by(raw_fieldname)
        return queryset

class QFilterBackend(FilterBackend):
    def filter_queryset(self, request, queryset, view):
        # NOTE: See migtration 0033_text_search_indexes
        q = request.query_params.get('q', None)
        if q:
            tsquery = "to_tsquery('simple', %s)"
            tsquery_params = [to_tsquery(q)]
            tsvector = """
             setweight(to_tsvector('simple',
                                   coalesce(accounts_account.name, '')), 'A') ||
             setweight(to_tsvector('simple',
                                   coalesce(inmutable_array_to_string(accounts_account.tags), '')), 'B') ||
             setweight(to_tsvector('simple',
                                   coalesce(accounts_account.description, '')), 'C')
            """

            select = {
                "rank": "ts_rank({tsvector},{tsquery})".format(tsquery=tsquery,
                                                               tsvector=tsvector),
            }
            select_params = tsquery_params
            where = ["{tsvector} @@ {tsquery}".format(tsquery=tsquery,
                                                      tsvector=tsvector), ]
            params = tsquery_params
            order_by = ["-rank", ]

            queryset = queryset.extra(select=select,
                                      select_params=select_params,
                                      where=where,
                                      params=params,
                                      order_by=order_by)
        return queryset

class CanViewAccountObjFilterBackend(FilterBackend):
    def filter_queryset(self, request, queryset, view):
        account_id = None

        # Filter by filter_fields
        if (hasattr(view, "filter_fields") and "account" in view.filter_fields and
                "account" in request.query_params):
            try:
                account_id = int(request.query_params["account"])
            except:
                logger.error("Filtering account diferent value than an integer: {}".format(
                    request.query_params["account"]
                ))
                raise BadRequest(_("'account' must be an integer value."))

        filter_expression = get_filter_expression_can_view_accounts(
            request.user,
            account_id)

        qs = queryset.filter(filter_expression)

        return super().filter_queryset(request, qs, view)

class DiscoverModeFilterBackend(FilterBackend):
    def filter_queryset(self, request, queryset, view):
        qs = queryset

        if "discover_mode" in request.query_params:
            field_data = request.query_params["discover_mode"]
            discover_mode = self._special_values_dict.get(field_data, field_data)

            if discover_mode:
                # discover_mode enabled
                qs = qs.filter(anon_permissions__contains=["view_account"],
                               blocked_code__isnull=True)

                # random order for featured accounts
                if request.query_params.get("is_featured", None) == 'true':
                    qs = qs.order_by("?")

        return super().filter_queryset(request, qs, view)

