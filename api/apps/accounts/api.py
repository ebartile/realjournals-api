import uuid
from django.db.models import Q
import json
from datetime import datetime, timezone
import requests
from django.shortcuts import render
from .models import Account, Membership, Broker, AccountRole
from . import utils as account_utils
from rest_framework import viewsets
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.decorators import action
from . import serializers
from apps.users import services as users_services
from rest_framework.response import Response
from django.apps import apps
from rest_framework import status
from apps.utils.exceptions import NotEnoughSlotsForAccount, WrongArguments, Blocked
from .permissions import IsAccountAdmin, HasAccountPerm, CanLeaveAccount
from . import filters as account_filters
from django.utils import timezone
from .choices import ANON_PERMISSIONS
from easy_thumbnails.source_generators import pil_image
from apps.notifications.choices import NotifyLevel
from . import services
from rest_framework.filters import SearchFilter, OrderingFilter
from .filters import BrokerFilter
from django_filters.rest_framework import DjangoFilterBackend
from apps.attachments.models import Attachment
from django.conf import settings
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from apps.utils.pagination import CustomPagination
import pytz
from apps.users.filters import CanViewAccountFilterBackend
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from apps.journals.models import HistoryOrders, HistoryDeals, Orders, Positions
from . import mt5
from django.core.exceptions import ValidationError

class AccountViewset(viewsets.ModelViewSet):
    queryset = Account.objects.all()
    serializer_class = serializers.AccountDetailSerializer
    permission_classes = [IsAuthenticated(),]
    pagination_class = CustomPagination
    filter_backends = (account_filters.UserOrderFilterBackend,
                       account_filters.QFilterBackend,
                       account_filters.CanViewAccountObjFilterBackend,
                       account_filters.DiscoverModeFilterBackend)
    filter_fields = (("member", "members"),
                     "is_featured")
    ordering = ("name", "id")

    def pre_conditions_blocked(self, obj):
        if obj is not None and self.is_blocked(obj):
            raise Blocked(_("This account is currently blocked"))

    def perform_update(self, serializer):
        obj = self.get_object()
        self.pre_conditions_blocked(obj)
        obj = serializer.save()

    def perform_destroy(self, instance):
        try:
            self.pre_conditions_blocked(instance)
            instance.delete()
        except Blocked as e:
            raise Blocked({"detail": str(e)})
        return Response(status=status.HTTP_204_NO_CONTENT)

    def is_blocked(self, obj):
        return obj.account is not None and obj.account.blocked_code is not None

    def get_permissions(self):
        if self.action == "retrieve" \
            or self.action == "stats" \
            or self.action == "watch" \
            or self.action == "list" \
            or self.action == "unwatch" \
            or self.action == "member_stats" \
            or self.action == "history_deals_get" \
            or self.action == "history_orders_get" \
            or self.action == "positions_get" \
            or self.action == "events" \
            or self.action == "orders_get" \
            or self.action == "stats" \
            or self.action == "by_slug":
            self.permission_classes = (HasAccountPerm("view_account"),)
        elif self.action == "update" \
            or self.action == "change_logo" \
            or self.action == "remove_logo" \
            or self.action == "partial" \
            or self.action == "upload_data" \
            or self.action == "create_trades" \
            or self.action == "destroy":
            self.permission_classes = (IsAccountAdmin(),)
        elif self.action == "leave":
            self.permission_classes = (CanLeaveAccount(),)
        return self.permission_classes

    def _get_order_by_field_name(self):
        order_by_query_param = account_filters.CanViewAccountObjFilterBackend.order_by_query_param
        order_by = self.request.GET.get(order_by_query_param, None)
        if order_by is not None and order_by.startswith("-"):
            return order_by[1:]

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.select_related("owner")

        if self.request.GET.get('discover_mode', False):
            qs = account_utils.attach_members(qs)
            qs = account_utils.attach_notify_policies(qs)
            qs = account_utils.attach_my_role_permissions(qs, user=self.request.user)
            qs = account_utils.attach_is_fan(qs, user=self.request.user)
        elif self.request.GET.get('slight', False):
            qs = account_utils.attach_basic_info(qs, user=self.request.user)
        else:
            qs = account_utils.attach_extra_info(qs, user=self.request.user)
        return qs

    def _set_base_permissions(self, obj):
        update_permissions = False
        if not obj.id:
            if not obj.is_private:
                # Creating a public account
                update_permissions = True
        else:
            if self.get_object().is_private != obj.is_private:
                # Changing account public state
                update_permissions = True

        if update_permissions:
            services.set_base_permissions_for_account(obj)

    def get_serializer(self, *args, **kwargs):
        if self.action == "list" and self.request.GET.get('slight', False):
            self.serializer_class = serializers.AccountSerializer
        if self.action == "create":
            self.serializer_class = serializers.AccountCreationSerializer
        if self.action == "create_trades":
            self.serializer_class = serializers.CreateTradesSerializer
        if self.action == "upload_data":
            self.serializer_class = serializers.UploadDataSerializer

        return super().get_serializer(*args, **kwargs)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        
        if not serializer.is_valid():
            raise WrongArguments(serializer.errors)  

        is_private = True

        total_memberships = 1
        (enough_slots, error_message) = users_services.has_available_slot_for_new_account(
            self.request.user,
            is_private,
            total_memberships
        )

        if not enough_slots:
            raise WrongArguments(_("No room left for more accounts."))

        username = serializer.data.get("username")
        password = serializer.data.get("password")
        server = serializer.data.get("server")
        broker = serializer.data.get("broker")
        timezone = serializer.data.get("timezone")
        currency = serializer.data.get("currency")
        trade_mode = serializer.data.get("trade_mode")
        account_type = serializer.data.get("account_type")
        name = serializer.data.get("name")
        company = serializer.data.get("company")
        billing_type = serializer.data.get("billing_type")
        is_monthly_billing = serializer.data.get("is_monthly_billing")

        broker = get_object_or_404(Broker, id=broker)

        Account = apps.get_model("accounts", "Account")
        account = Account.objects.filter(username=username)
        if account.count() > 0:
            raise WrongArguments(_("Account {} - {} Already exists.".format(account[0].username, account[0].server)))

        new_account = Account(
            owner=request.user,
            username=username,
            server=server,
            broker=broker,
            billing_type=billing_type,
            is_monthly_billing=is_monthly_billing,
            is_private=is_private
        )
        
        if account_type == "MANUAL":
            new_account.timezone = timezone
            new_account.currency = currency
            new_account.trade_mode = trade_mode
            new_account.account_type = account_type
            new_account.company = company
            new_account.name = name
            new_account.has_be_configured = True
        else:
            new_account.password = password

        if new_account.is_private:
            new_account.anon_permissions = []
            new_account.public_permissions = []
        else:
            anon_permissions = list(map(lambda perm: perm[0], ANON_PERMISSIONS))
            existing_anon_permissions = new_account.anon_permissions or []
            existing_public_permissions = new_account.public_permissions or []
            
            new_account.anon_permissions = list(set(existing_anon_permissions + anon_permissions))
            new_account.public_permissions = list(set(existing_public_permissions + anon_permissions))

        new_account.save()

        instance = self.get_queryset().get(id=new_account.id)
        serializer = serializers.AccountDetailSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['POST'])
    def upload_data(self, request, *args, **kwargs):
        """
        Upload to this account.
        """
        self.object = get_object_or_404(self.get_queryset(), **kwargs)

        if self.is_blocked(self.object):
            raise Blocked(_("This account is currently blocked"))

        serializer = serializers.UploadDataSerializer(data=request.data)
        if not serializer.is_valid():
            raise WrongArguments(serializer.errors)

        data = serializer.data
        broker = get_object_or_404(Broker, id=data.get('broker', None))

        self.object.timezone = data.get('timezone')
        self.object.broker = broker
        self.object.save(update_fields=["broker", "timezone",])

        return Response(status=status.HTTP_201_CREATED)


    #@method_decorator(cache_page(60*5))
    def retrieve(self, request, *args, **kwargs):
        qs = self.get_queryset()
        if self.action == "by_slug":
            self.lookup_field = "slug"
            # If we retrieve the account by slug we want to filter by user the
            # permissions and return 404 in case the user don't have access
            flt = account_filters.get_filter_expression_can_view_accounts(
                self.request.user)

            qs = qs.filter(flt)

        self.object = get_object_or_404(qs, **kwargs)

        if self.object is None:
            raise Http404

        serializer = self.get_serializer(self.object)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['POST'])
    def change_logo(self, request, *args, **kwargs):
        """
        Change logo to this account.
        """
        self.object = get_object_or_404(self.get_queryset(), **kwargs)

        logo = request.FILES.get('file', None)
        if not logo:
            raise WrongArguments(_("Incomplete arguments"))
        try:
            pil_image(logo)
        except Exception:
            raise WrongArguments(_("Invalid image format"))

        if self.is_blocked(self.object):
            raise Blocked(_("This account is currently blocked"))

        self.object.logo = logo
        self.object.save(update_fields=["logo"])

        serializer = self.get_serializer(self.object)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['POST'])
    def remove_logo(self, request, *args, **kwargs):
        """
        Remove the logo of a account.
        """
        self.object = get_object_or_404(self.get_queryset(), **kwargs)

        if self.is_blocked(self.object):
            raise Blocked(_("This account is currently blocked"))

        self.object.logo = None
        self.object.save(update_fields=["logo"])

        serializer = self.get_serializer(self.object)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['POST'])
    def watch(self, request, pk=None):
        account = self.get_object()

        if account and self.is_blocked(account):
            raise Blocked(_("This account is currently blocked"))

        notify_level = request.data.get("notify_level", NotifyLevel.involved)
        account.add_watcher(self.request.user, notify_level=notify_level)
        return Response(status=status.HTTP_200_OK)

    @action(detail=True, methods=['POST'])
    def unwatch(self, request, pk=None):
        account = self.get_object()

        if account and self.is_blocked(account):
            raise Blocked(_("This account is currently blocked"))

        user = self.request.user
        account.remove_watcher(user)
        return Response(status=status.HTTP_200_OK)

    @action(detail=True, methods=['POST'])
    def leave(self, request, pk=None):
        account = self.get_object()

        if account and self.is_blocked(account):
            raise Blocked(_("This account is currently blocked"))

        services.remove_user_from_account(request.user, account)
        return Response(status=status.HTTP_200_OK)

    @action(detail=False, methods=['GET'])
    def by_slug(self, request, *args, **kwargs):
        slug = request.GET.get("slug", None)
        return self.retrieve(request, slug=slug)

    def pre_delete(self, obj):
        move_to = self.request.GET.get('moveTo', None)
        if move_to:
            membership_model = apps.get_model("accounts", "Membership")
            role_dest = get_object_or_404(self.model, account=obj.account, id=move_to)
            qs = membership_model.objects.filter(account_id=obj.account.pk, role=obj)
            qs.update(role=role_dest)

        services.orphan_account(obj)
        if settings.CELERY_ENABLED:
            services.delete_account.delay(obj.id)
        else:
            services.delete_account(obj.id)

    def perform_destroy(self, instance):
        try:
            self.pre_conditions_blocked(instance)
            self.pre_delete(instance)
        except Blocked as e:
            raise Blocked({"detail": str(e)})
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['GET'])
    def symbol_info(self, request, *args, **kwargs):
        instance = self.get_object()
        symbol = request.query_params.get('symbol', '')
        symbol_info = instance.symbol_info(symbol)
        # Serialize the 'symbol_info' to return as a response
        # You might need to create a serializer for the symbol info data
        return Response(symbol_info._asdict(), status=status.HTTP_200_OK)

    @action(detail=True, methods=['GET'])
    def orders_get(self, request, *args, **kwargs):
        instance = self.get_object()
        group = request.GET.get('group', '')
        ticket = request.GET.get('ticket', '')
        symbol = request.GET.get('symbol', '')
        kwargs = {key: value for key, value in (('group', group), ('ticket', ticket), ('symbol', symbol)) if value}
        orders = Orders.objects(account=instance.id, **kwargs).order_by('-time_setup')
        paginator = CustomPagination()
        result_page = paginator.paginate_queryset(orders, request)                
        serialized_orders = serializers.OrdersSerializer(result_page, many=True).data
        paginated_response = {
            'count': paginator.page.paginator.count,
            'next': paginator.get_next_link(),
            'previous': paginator.get_previous_link(),
            'results': serialized_orders
        }
        return Response(paginated_response, status=status.HTTP_200_OK)

    @action(detail=True, methods=['GET'])
    def positions_get(self, request, *args, **kwargs):
        instance = self.get_object()
        group = request.GET.get('group', '')
        ticket = request.GET.get('ticket', '')
        symbol = request.GET.get('symbol', '')
        kwargs = {key: value for key, value in (('group', group), ('ticket', ticket), ('symbol', symbol)) if value}
        positions = Positions.objects(account=instance.id, **kwargs).order_by('-time')
        paginator = CustomPagination()
        result_page = paginator.paginate_queryset(positions, request)                
        serialized_positions = serializers.TradePositionSerializer(result_page, many=True).data
        paginated_response = {
            'count': paginator.page.paginator.count,
            'next': paginator.get_next_link(),
            'previous': paginator.get_previous_link(),
            'results': serialized_positions
        }
        return Response(paginated_response, status=status.HTTP_200_OK)

    @action(detail=True, methods=['GET'])
    def history_orders_get(self, request, *args, **kwargs):
        instance = self.get_object()
        date_from = request.GET.get('date_from', instance.start_date.strftime("%Y-%m-%dT%H:%M:%SZ"))
        date_to = request.GET.get('date_to', instance.end_date.strftime("%Y-%m-%dT%H:%M:%SZ"))
        group = request.GET.get('group', '')
        ticket = request.GET.get('ticket', '')
        position = request.GET.get('position', '')
        state = request.GET.getlist('state')
        date_format = "%Y-%m-%dT%H:%M:%SZ"
        date_from = int(datetime.strptime(date_from, date_format).timestamp())
        date_to = int(datetime.strptime(date_to, date_format).timestamp())
        kwargs = {key: value for key, value in (('group', group), ('ticket', ticket), ('position', position)) if value}
        result = HistoryOrders.objects(account=instance.id, time_setup__gte=date_from, time_setup__lte=date_to, **kwargs).order_by('-time_setup')
        if state:
            result = result.filter(state__in=state)
        paginator = CustomPagination()
        result_page = paginator.paginate_queryset(result, request)                
        serialized_history_orders = serializers.OrdersSerializer(result_page, many=True).data
        paginated_response = {
            'count': paginator.page.paginator.count,
            'next': paginator.get_next_link(),
            'previous': paginator.get_previous_link(),
            'results': serialized_history_orders
        }
        return Response(paginated_response, status=status.HTTP_200_OK)

    @action(detail=True, methods=['GET'])
    def history_deals_get(self, request, *args, **kwargs):
        instance = self.get_object()
        date_from = request.GET.get('date_from', instance.start_date.strftime("%Y-%m-%dT%H:%M:%SZ"))
        date_to = request.GET.get('date_to', instance.end_date.strftime("%Y-%m-%dT%H:%M:%SZ"))
        group = request.GET.get('group', '')
        ticket = request.GET.get('ticket', '')
        position = request.GET.get('position', '')
        deal_type = request.GET.getlist('type')
        entry = request.GET.getlist('entry')
        date_format = "%Y-%m-%dT%H:%M:%SZ"
        date_from = int(datetime.strptime(date_from, date_format).timestamp())
        date_to = int(datetime.strptime(date_to, date_format).timestamp())
        kwargs = {key: value for key, value in (('group', group), ('ticket', ticket), ('position', position)) if value}
        result = HistoryDeals.objects(account=instance.id, time__gte=date_from, time__lte=date_to, **kwargs).order_by('-time')
        if deal_type:
            result = result.filter(type__in=deal_type)
        if entry:
            result = result.filter(entry__in=entry)
        paginator = CustomPagination()
        page = paginator.paginate_queryset(result, request)
        serialized_history_deals = serializers.HistoryDealsSerializer(page, many=True).data
        paginated_response = {
            'count': paginator.page.paginator.count,
            'next': paginator.get_next_link(),
            'previous': paginator.get_previous_link(),
            'results': serialized_history_deals
        }
        return Response(paginated_response, status=status.HTTP_200_OK)

    @action(detail=True, methods=['GET'])
    def stats(self, request, *args, **kwargs):
        instance = self.get_object()
        date_from = request.GET.get('date_from', instance.start_date.strftime("%Y-%m-%dT%H:%M:%SZ"))
        date_to = request.GET.get('date_to', instance.end_date.strftime("%Y-%m-%dT%H:%M:%SZ"))
        date_format = "%Y-%m-%dT%H:%M:%SZ"
        date_from = int(datetime.strptime(date_from, date_format).timestamp())
        date_to = int(datetime.strptime(date_to, date_format).timestamp())
        deals = HistoryDeals.objects(account=instance.id, time__gte=date_from, time__lte=date_to).order_by('-time')
        positions = Positions.objects(account=instance.id)

        pipeline = [
            {"$group": {
                "_id": "$symbol",
                "trade_allocation_amounts": {"$sum": {"$multiply": ["$volume", "$price"]}}
            }}
        ]
        aggregated_data = deals.aggregate(*pipeline)

        trade_allocation_amounts = []
        trade_allocation_categories = []

        for data in aggregated_data:
            if data['_id']:
                trade_allocation_categories.append(data['_id'])
                trade_allocation_amounts.append(data['trade_allocation_amounts'])

        daily_cumulative_pl = defaultdict(float)
        for deal in deals.filter(entry=1):
            deal_date = datetime.utcfromtimestamp(deal.time).date()
            daily_cumulative_pl[deal_date] += deal.profit

        # Convert the daily cumulative profit and loss dictionary into a list of dicts
        net_profit_loss_data = [pl for date, pl in daily_cumulative_pl.items()]
        net_profit_loss_labels = [date for date, pl in daily_cumulative_pl.items()]

        response = {
            'total_trades': deals.filter(entry=1).count() + positions.filter().count(),
            'total_winning_trades': deals.filter(entry=1, profit__gte=0).count() + positions.filter(profit__gte=0).count(),
            'total_lossing_trades': deals.filter(entry=1, profit__lt=0).count() + positions.filter(profit__lt=0).count(),
            'net_profit': sum(deal.profit for deal in deals.filter(entry=1, profit__gte=0)) + sum(position.profit for position in positions.filter(profit__gte=0)),
            'net_loss': sum(deal.profit for deal in deals.filter(entry=1, profit__lt=0)) + sum(position.profit for position in positions.filter(profit__lt=0)),
            'net_profit_loss_data': net_profit_loss_data,
            'net_profit_loss_labels': net_profit_loss_labels,
            'trade_allocation_amounts': trade_allocation_amounts,
            'trade_allocation_categories': trade_allocation_categories
        }
        return Response(response, status=status.HTTP_200_OK)

    @action(detail=True, methods=['GET'])
    def events(self, request, *args, **kwargs):
        response = [{
            "id": "e99f09a7-dd88-49d5-b1c8-1daf80c2d7b2",
            "allDay": False,
            "color": "#00A76F",
            "description": "Atque eaque ducimus minima distinctio velit. Laborum et veniam officiis. Delectus ex saepe hic id laboriosam officia. Odit nostrum qui illum saepe debitis ullam. Laudantium beatae modi fugit ut. Dolores consequatur beatae nihil voluptates rem maiores.",
            "start": 1704701218000,
            "end": 1704751218000,
            "title": "The Ultimate Guide to Productivity Hacks"
        }]
        return Response(response, status=status.HTTP_200_OK)

    @action(detail=True, methods=['POST'])
    def create_trades(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = serializers.CreateTradesSerializer(data=request.data)
        
        if not serializer.is_valid():
            raise WrongArguments(serializer.errors)

        history_deals = serializer.data.get("history_deals", [])
        for history_deal in history_deals:           
            result = HistoryDeals.objects(account=instance.id, ticket=history_deal['ticket']).first()
            if result:
                print("updating history deal")   
                result.update(**history_deal)
            else:
                print("creating history deal")   
                history_deal['account'] = instance.id
                new_deal = HistoryDeals(**history_deal)
                new_deal.save()

        history_orders = serializer.data.get("history_orders", [])
        for history_order in history_orders:           
            result = HistoryOrders.objects(account=instance.id, ticket=history_order['ticket']).first()
            if result:
                print("updating history order")   
                result.update(**history_order)
            else:
                print("creating history order")   
                history_order['account'] = instance.id
                new_order = HistoryOrders(**history_order)
                new_order.save()

        positions = serializer.data.get("positions", [])
        Positions.objects(account=instance.id).delete()
        for position in positions:           
            print("creating position")   
            position['account'] = instance.id
            new_position = Positions(**position)
            new_position.save()

        orders = serializer.data.get("orders", [])
        Orders.objects(account=instance.id).delete()
        for order in orders:           
            print("creating order")   
            order['account'] = instance.id
            new_order = Orders(**order)
            new_order.save()

        return Response(status=status.HTTP_200_OK)

class BrokerViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Broker.objects.filter(is_enabled=True)
    serializer_class = serializers.BrokerSerializer
    permission_classes = (AllowAny,)
    filter_backends = [DjangoFilterBackend]
    filterset_class = BrokerFilter

######################################################
# Role
######################################################

class RolesViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.RoleSerializer
    permission_classes = (IsAccountAdmin(),)

    def get_queryset(self):
        qs = AccountRole.objects.filter(account=self.kwargs['id'])
        return qs

    def get_permissions(self):
        if self.action == "list":
            self.permission_classes = (AllowAny(),)
        elif self.action == "retrieve":
            self.permission_classes = (HasAccountPerm("view_account"),)

        return self.permission_classes

    def pre_conditions_blocked(self, obj):
        if obj is not None and self.is_blocked(obj):
            raise Blocked(_("This account is currently blocked"))

    def perform_create(self, serializer):
        obj = serializer.save()
        self.pre_conditions_blocked(obj)

    def perform_update(self, serializer):
        obj = self.get_object()
        self.pre_conditions_blocked(obj)
        serializer.save()

    def is_blocked(self, obj):
        return obj.account is not None and obj.account.blocked_code is not None

    def pre_delete(self, obj):
        move_to = self.request.GET.get('moveTo', None)
        if move_to:
            membership_model = apps.get_model("accounts", "Membership")
            role_dest = get_object_or_404(self.model, account=obj.account, id=move_to)
            qs = membership_model.objects.filter(account_id=obj.account.pk, role=obj)
            qs.update(role=role_dest)

        super().pre_delete(obj)

    def perform_destroy(self, instance):
        try:
            self.pre_conditions_blocked(instance)
            self.pre_delete(instance)
            instance.delete()
        except Blocked as e:
            raise Blocked({"detail": str(e)})
        return Response(status=status.HTTP_204_NO_CONTENT)

######################################################
## Members & Invitations
######################################################

class MembershipViewSet(viewsets.ModelViewSet):
    admin_serializer_class = serializers.MembershipAdminSerializer
    serializer_class = serializers.MembershipSerializer
    permission_classes = (IsAccountAdmin(),)
    filter_backends = (CanViewAccountFilterBackend,)
    filter_fields = ("account", "role")
    pagination_class = CustomPagination

    def get_queryset(self):
        qs = Membership.objects.filter(account=self.kwargs['id'])
        return qs

    def get_permissions(self):
        if self.action == "list":
            self.permission_classes = (AllowAny(),)
        elif self.action == "retrieve":
            self.permission_classes = (HasAccountPerm("view_account"),)

        return self.permission_classes

    def get_serializer(self, *args, **kwargs):
        use_admin_serializer = False

        if self.action == "retrieve":
            self.object = self.get_object()
            use_admin_serializer = services.is_account_admin(self.request.user, self.object.account)

        account_id = self.request.query_params.get("account", None)
        if self.action == "list" and account_id is not None:
            account = get_object_or_404(Account, pk=account_id)
            use_admin_serializer = permissions_services.is_account_admin(self.request.user, account)

        if use_admin_serializer:
            self.serializer_class = self.admin_serializer_class

        if self.action == "create":
            self.serializer_class = serializers.MembershipCreateSerializer

        return super().get_serializer(*args, **kwargs)

    def is_blocked(self, obj):
        return obj.account is not None and obj.account.blocked_code is not None

    def _check_if_account_can_have_more_memberships(self, account, total_new_memberships):
        (can_add_memberships, error_type) = services.check_if_account_can_have_more_memberships(
            account,
            total_new_memberships
        )
        if not can_add_memberships:
            raise WrongArguments(_("No room left for more accounts."))

    @action(detail=True, methods=['POST', 'GET'])
    def resend_invitation(self, request, **kwargs):
        invitation = self.get_object()
        services.send_invitation(invitation=invitation)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_destroy(self, obj):
        self.pre_conditions_blocked(obj)
        if obj.user is not None and not services.can_user_leave_account(obj.user, obj.account):
            raise WrongArguments(_("The account must have an owner and at least one of the users "
                                "must be an active admin"))
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def pre_conditions_blocked(self, obj):
        if obj is not None and self.is_blocked(obj):
            raise Blocked(_("This account is currently blocked"))

    def perform_create(self, serializer):
        self.account = get_object_or_404(Account, id=self.kwargs['id'])
        self._validate_member_doesnt_exist(serializer.validated_data.get('email'))
        self._check_if_account_can_have_more_memberships(self.account, 1)
        obj = serializer.save(token = str(uuid.uuid1()), invited_by = self.request.user, user = services.find_invited_user(serializer.validated_data.get("email"), default=serializer.user), account=self.account)
        # Send email only if a new membership is created
        services.send_invitation(invitation=obj)

    def perform_update(self, serializer):
        obj = self.get_object()
        self.pre_conditions_blocked(obj)
        obj = serializer.save()
        obj.invited_by = self.request.user
        obj.user = services.find_invited_user(obj.email)

    def _validate_member_doesnt_exist(self, email):
        qs = Membership.objects.all()
        qs = qs.filter(Q(account_id=self.account.id, user__email=email) |
                       Q(account_id=self.account.id, email=email))

        if qs.count() > 0:
            raise ValidationError(_("The user already exists in the account"))

class InvitationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Only used by front for get invitation by it token.
    """
    queryset = Membership.objects.filter(user__isnull=True)
    serializer_class = serializers.MembershipSerializer
    lookup_field = "token"
    permission_classes = (AllowAny,)

    def list(self, *args, **kwargs):
        raise WrongArguments(_("You don't have permissions to see that."))
