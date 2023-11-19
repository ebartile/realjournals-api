from django.shortcuts import render
from .models import Account, Membership, Broker
from . import utils as account_utils
from rest_framework import viewsets
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.decorators import action
from . import serializers
from apps.users import services as users_services
from .apps import connect_accounts_signals, disconnect_accounts_signals
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
from .tasks import process_import_task
from apps.attachments.models import Attachment

class AccountViewset(viewsets.ModelViewSet):
    queryset = Account.objects.all()
    permission_classes = [IsAuthenticated(),]
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

    def perform_create(self, serializer):
        obj = serializer.save()
        self.pre_conditions_blocked(obj)

    def perform_update(self, serializer):
        obj = serializer.save()
        self.pre_conditions_blocked(obj)

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
            or self.action == "like" \
            or self.action == "unlike" \
            or self.action == "watch" \
            or self.action == "unwatch" \
            or self.action == "member_stats" \
            or self.action == "journal_stats" \
            or self.action == "by_slug":
            self.permission_classes = (HasAccountPerm("view_account"),)
        elif self.action == "update" \
            or self.action == "modules" \
            or self.action == "change_logo" \
            or self.action == "remove_logo" \
            or self.action == "partial" \
            or self.action == "upload_data" \
            or self.action == "destroy":
            self.permission_classes = (IsAccountAdmin(),)
        elif self.action == "watch" \
            or self.action == "unwatch":
            self.permission_classes = (IsAuthenticated(),HasAccountPerm("view_account"))
        elif self.action == "list":
            self.permission_classes = (AllowAny(),)
        elif self.action == "leave":
            self.permission_classes = (CanLeaveAccount(),)
        return self.permission_classes

    def _get_order_by_field_name(self):
        order_by_query_param = account_filters.CanViewAccountObjFilterBackend.order_by_query_param
        order_by = self.request.query_params.get(order_by_query_param, None)
        if order_by is not None and order_by.startswith("-"):
            return order_by[1:]

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.select_related("owner")

        if self.request.query_params.get('discover_mode', False):
            qs = account_utils.attach_members(qs)
            qs = account_utils.attach_notify_policies(qs)
            qs = account_utils.attach_my_role_permissions(qs, user=self.request.user)
            qs = account_utils.attach_is_fan(qs, user=self.request.user)
        elif self.request.query_params.get('slight', False):
            qs = account_utils.attach_basic_info(qs, user=self.request.user)
        else:
            qs = account_utils.attach_extra_info(qs, user=self.request.user)
        return qs


    def get_serializer_class(self):
        if self.action == "list" and self.request.query_params.get('slight', False):
            return serializers.AccountSerializer
        if self.action == "create":
            return serializers.AccountCreateSerializer
        if self.action == "upload_data":
            return serializers.UploadDataSerializer
        return serializers.AccountDetailSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        
        if not serializer.is_valid():
            raise WrongArguments(serializer.errors)  

        name = str(serializer.data.get("name", None))
        description = str(serializer.data.get("description", None))
        is_private = str(serializer.data.get("is_private", True))

        total_memberships = 1
        (enough_slots, error_message) = users_services.has_available_slot_for_new_account(
            self.request.user,
            is_private,
            total_memberships
        )

        if not enough_slots:
            raise NotEnoughSlotsForAccount(_("No room left for more accounts."))

        disconnect_accounts_signals()
        Account = apps.get_model("accounts", "Account")
        new_account = Account(
            owner=request.user,
            name=name,
            description=description,
            is_private=is_private
        )
        if new_account.is_private:
            new_account.anon_permissions = []
            new_account.public_permissions = []
        else:
            # If a account is public anonymous and registered users should have at
            # least visualization permissions.
            anon_permissions = list(map(lambda perm: perm[0], ANON_PERMISSIONS))
            new_account.anon_permissions = list(set((new_account.anon_permissions or []) + anon_permissions))
            new_account.public_permissions = list(set((new_account.public_permissions or []) + anon_permissions))

        new_account.save()
        connect_accounts_signals()

        instance = self.get_queryset().get(id=new_account.id)
        serializer = serializers.AccountDetailSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        qs = self.get_queryset()
        if self.action == "by_slug":
            self.lookup_field = "slug"
            # If we retrieve the account by slug we want to filter by user the
            # permissions and return 404 in case the user don't have access
            flt = filters.get_filter_expression_can_view_accounts(
                self.request.user)

            qs = qs.filter(flt)

        self.object = get_object_or_404(qs, **kwargs)

        if self.object is None:
            raise Http404

        serializer = self.get_serializer(self.object)
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

        process_import_task.delay(data.get('attachment'), request.user.id)

        return Response(status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['POST'])
    def change_logo(self, request, *args, **kwargs):
        """
        Change logo to this account.
        """
        self.object = get_object_or_404(self.get_queryset(), **kwargs)

        logo = request.FILES.get('logo', None)
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
        slug = request.query_params.get("slug", None)
        return self.retrieve(request, slug=slug)

    @action(detail=False, methods=['POST'])
    def bulk_update_order(self, request, **kwargs):
        if self.request.user.is_anonymous:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        serializer = serializers.UpdateAccountOrderBulkSerializer(data=request.data, many=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.data
        services.update_accounts_order_in_bulk(data, "user_order", request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['GET', 'PATCH'])
    def modules(self, request, pk=None):
        pass

    def destroy(self, request, *args, **kwargs):
        pass

    @action(detail=True, methods=['GET'])
    def last_error(self, request, *args, **kwargs):
        instance = self.get_object()
        error = instance.last_error()
        # Serialize the 'error' to return as a response
        # You might need to create a serializer for the error data
        serialized_error = ErrorSerializer(error).data
        return Response(serialized_error, status=status.HTTP_200_OK)

    @action(detail=True, methods=['GET'])
    def version(self, request, *args, **kwargs):
        instance = self.get_object()
        version_info = instance.version()
        # Serialize the 'version_info' to return as a response
        # You might need to create a serializer for the version data
        serialized_version = VersionInfoSerializer(version_info).data
        return Response(serialized_version, status=status.HTTP_200_OK)

    @action(detail=True, methods=['GET'])
    def terminal_info(self, request, *args, **kwargs):
        instance = self.get_object()
        terminal_info = instance.terminal_info()
        # Serialize the 'terminal_info' to return as a response
        # You might need to create a serializer for the terminal info data
        serialized_terminal_info = TerminalInfoSerializer(terminal_info).data
        return Response(serialized_terminal_info, status=status.HTTP_200_OK)

    @action(detail=True, methods=['GET'])
    def symbols_total(self, request, *args, **kwargs):
        instance = self.get_object()
        total_symbols = instance.symbols_total()
        return Response({'total_symbols': total_symbols}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['GET'])
    def symbols_get(self, request, *args, **kwargs):
        instance = self.get_object()
        group = request.query_params.get('group', '')
        symbols = instance.symbols_get(group)
        # Serialize the 'symbols' to return as a response
        # You might need to create a serializer for the symbols data
        serialized_symbols = SymbolInfoSerializer(symbols, many=True).data
        return Response(serialized_symbols, status=status.HTTP_200_OK)

    @action(detail=True, methods=['GET'])
    def has_symbol(self, request, *args, **kwargs):
        instance = self.get_object()
        symbol_param = request.query_params.get('symbol', '')
        has_symbol = instance.has_symbol(symbol_param)
        return Response({'has_symbol': has_symbol}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['GET'])
    def symbol_info(self, request, *args, **kwargs):
        instance = self.get_object()
        symbol = request.query_params.get('symbol', '')
        symbol_info = instance.symbol_info(symbol)
        # Serialize the 'symbol_info' to return as a response
        # You might need to create a serializer for the symbol info data
        serialized_symbol_info = SymbolInfoSerializer(symbol_info).data
        return Response(serialized_symbol_info, status=status.HTTP_200_OK)

    @action(detail=True, methods=['GET'])
    def symbol_info_tick(self, request, *args, **kwargs):
        instance = self.get_object()
        symbol = request.query_params.get('symbol', '')
        tick_info = instance.symbol_info_tick(symbol)
        # Serialize the 'tick_info' to return as a response
        # You might need to create a serializer for the tick info data
        serialized_tick_info = TickInfoSerializer(tick_info).data
        return Response(serialized_tick_info, status=status.HTTP_200_OK)

    @action(detail=True, methods=['GET'])
    def market_book_add(self, request, *args, **kwargs):
        instance = self.get_object()
        symbol = request.query_params.get('symbol', '')
        result = instance.market_book_add(symbol)
        return Response({'success': result}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['GET'])
    def market_book_get(self, request, *args, **kwargs):
        instance = self.get_object()
        symbol = request.query_params.get('symbol', '')
        book_content = instance.market_book_get(symbol)
        # Serialize the 'book_content' to return as a response
        # You might need to create a serializer for the book content data
        serialized_book_content = BookContentSerializer(book_content).data
        return Response(serialized_book_content, status=status.HTTP_200_OK)

    @action(detail=True, methods=['GET'])
    def market_book_release(self, request, *args, **kwargs):
        instance = self.get_object()
        symbol = request.query_params.get('symbol', '')
        result = instance.market_book_release(symbol)
        return Response({'success': result}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['GET'])
    def copy_rates_from(self, request, *args, **kwargs):
        instance = self.get_object()
        symbol = request.query_params.get('symbol', '')
        timeframe = request.query_params.get('timeframe', '')
        date_from = request.query_params.get('date_from', '')
        count = request.query_params.get('count', '')
        rates = instance.copy_rates_from(symbol, timeframe, date_from, count)
        # Serialize the 'rates' to return as a response
        # You might need to create a serializer for the rates data
        serialized_rates = RatesSerializer(rates).data
        return Response(serialized_rates, status=status.HTTP_200_OK)

    @action(detail=True, methods=['GET'])
    def copy_rates_from_pos(self, request, *args, **kwargs):
        instance = self.get_object()
        symbol = request.query_params.get('symbol', '')
        timeframe = request.query_params.get('timeframe', '')
        start_pos = request.query_params.get('start_pos', '')
        count = request.query_params.get('count', '')
        rates = instance.copy_rates_from_pos(symbol, timeframe, start_pos, count)
        # Serialize the 'rates' to return as a response
        # You might need to create a serializer for the rates data
        serialized_rates = RatesSerializer(rates).data
        return Response(serialized_rates, status=status.HTTP_200_OK)

    @action(detail=True, methods=['GET'])
    def copy_rates_range(self, request, *args, **kwargs):
        instance = self.get_object()
        symbol = request.query_params.get('symbol', '')
        timeframe = request.query_params.get('timeframe', '')
        date_from = request.query_params.get('date_from', '')
        date_to = request.query_params.get('date_to', '')
        rates = instance.copy_rates_range(symbol, timeframe, date_from, date_to)
        # Serialize the 'rates' to return as a response
        # You might need to create a serializer for the rates data
        serialized_rates = RatesSerializer(rates).data
        return Response(serialized_rates, status=status.HTTP_200_OK)

    @action(detail=True, methods=['GET'])
    def copy_ticks_from(self, request, *args, **kwargs):
        instance = self.get_object()
        symbol = request.query_params.get('symbol', '')
        date_from = request.query_params.get('date_from', '')
        count = request.query_params.get('count', '')
        flags = request.query_params.get('flags', '')
        ticks = instance.copy_ticks_from(symbol, date_from, count, flags)
        # Serialize the 'ticks' to return as a response
        # You might need to create a serializer for the ticks data
        serialized_ticks = TicksSerializer(ticks).data
        return Response(serialized_ticks, status=status.HTTP_200_OK)

    @action(detail=True, methods=['GET'])
    def copy_ticks_range(self, request, *args, **kwargs):
        instance = self.get_object()
        symbol = request.query_params.get('symbol', '')
        date_from = request.query_params.get('date_from', '')
        date_to = request.query_params.get('date_to', '')
        flags = request.query_params.get('flags', '')
        ticks = instance.copy_ticks_range(symbol, date_from, date_to, flags)
        # Serialize the 'ticks' to return as a response
        # You might need to create a serializer for the ticks data
        serialized_ticks = TicksSerializer(ticks).data
        return Response(serialized_ticks, status=status.HTTP_200_OK)

    @action(detail=True, methods=['GET'])
    def orders_total(self, request, *args, **kwargs):
        instance = self.get_object()
        total_orders = instance.orders_total()
        return Response({'total_orders': total_orders}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['GET'])
    def orders_get(self, request, *args, **kwargs):
        instance = self.get_object()
        group = request.query_params.get('group', '')
        ticket = request.query_params.get('ticket', '')
        symbol = request.query_params.get('symbol', '')
        orders = instance.orders_get(group=group, ticket=ticket, symbol=symbol)
        # Serialize the 'orders' to return as a response
        # You might need to create a serializer for the orders data
        serialized_orders = OrdersSerializer(orders).data
        return Response(serialized_orders, status=status.HTTP_200_OK)

    @action(detail=True, methods=['GET'])
    def order_calc_margin(self, request, *args, **kwargs):
        instance = self.get_object()
        action = request.query_params.get('action', '')
        symbol = request.query_params.get('symbol', '')
        volume = request.query_params.get('volume', '')
        price = request.query_params.get('price', '')
        calculated_margin = instance.order_calc_margin(action, symbol, volume, price)
        return Response({'calculated_margin': calculated_margin}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['GET'])
    def order_calc_profit(self, request, *args, **kwargs):
        instance = self.get_object()
        action = request.query_params.get('action', '')
        symbol = request.query_params.get('symbol', '')
        volume = request.query_params.get('volume', '')
        price_open = request.query_params.get('price_open', '')
        price_close = request.query_params.get('price_close', '')
        calculated_profit = instance.order_calc_profit(action, symbol, volume, price_open, price_close)
        return Response({'calculated_profit': calculated_profit}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['GET'])
    def order_check(self, request, *args, **kwargs):
        instance = self.get_object()
        request_data = request.data  # Adjust as per your request data structure
        order_check_result = instance.order_check(request_data)
        # Serialize the 'order_check_result' to return as a response
        # You might need to create a serializer for the order check result
        serialized_result = OrderCheckResultSerializer(order_check_result).data
        return Response(serialized_result, status=status.HTTP_200_OK)

    @action(detail=True, methods=['GET'])
    def order_send(self, request, *args, **kwargs):
        instance = self.get_object()
        request_data = request.data  # Adjust as per your request data structure
        order_send_result = instance.order_send(request_data)
        # Serialize the 'order_send_result' to return as a response
        # You might need to create a serializer for the order send result
        serialized_result = OrderSendResultSerializer(order_send_result).data
        return Response(serialized_result, status=status.HTTP_200_OK)

    @action(detail=True, methods=['GET'])
    def positions_total(self, request, *args, **kwargs):
        instance = self.get_object()
        total_positions = instance.positions_total()
        return Response({'total_positions': total_positions}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['GET'])
    def positions_get(self, request, *args, **kwargs):
        instance = self.get_object()
        group = request.query_params.get('group', '')
        ticket = request.query_params.get('ticket', '')
        symbol = request.query_params.get('symbol', '')
        positions = instance.positions_get(group=group, ticket=ticket, symbol=symbol)
        # Serialize the 'positions' to return as a response
        # You might need to create a serializer for the positions data
        serialized_positions = PositionsSerializer(positions).data
        return Response(serialized_positions, status=status.HTTP_200_OK)

    @action(detail=True, methods=['GET'])
    def history_orders_total(self, request, *args, **kwargs):
        instance = self.get_object()
        date_from = request.query_params.get('date_from', '')
        date_to = request.query_params.get('date_to', '')
        total_history_orders = instance.history_orders_total(date_from, date_to)
        return Response({'total_history_orders': total_history_orders}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['GET'])
    def history_orders_get(self, request, *args, **kwargs):
        instance = self.get_object()
        date_from = request.query_params.get('date_from', '')
        date_to = request.query_params.get('date_to', '')
        group = request.query_params.get('group', '')
        ticket = request.query_params.get('ticket', '')
        position = request.query_params.get('position', '')
        history_orders = instance.history_orders_get(date_from=date_from, date_to=date_to, group=group, ticket=ticket, position=position)
        # Serialize the 'history_orders' to return as a response
        # You might need to create a serializer for the history orders data
        serialized_history_orders = HistoryOrdersSerializer(history_orders).data
        return Response(serialized_history_orders, status=status.HTTP_200_OK)

    @action(detail=True, methods=['GET'])
    def history_deals_total(self, request, *args, **kwargs):
        instance = self.get_object()
        date_from = request.query_params.get('date_from', '')
        date_to = request.query_params.get('date_to', '')
        total_history_deals = instance.history_deals_total(date_from, date_to)
        return Response({'total_history_deals': total_history_deals}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['GET'])
    def history_deals_get(self, request, *args, **kwargs):
        instance = self.get_object()
        date_from = request.query_params.get('date_from', '')
        date_to = request.query_params.get('date_to', '')
        group = request.query_params.get('group', '')
        ticket = request.query_params.get('ticket', '')
        position = request.query_params.get('position', '')
        history_deals = instance.history_deals_get(date_from=date_from, date_to=date_to, group=group, ticket=ticket, position=position)
        # Serialize the 'history_deals' to return as a response
        # You might need to create a serializer for the history deals data
        serialized_history_deals = HistoryDealsSerializer(history_deals).data
        return Response(serialized_history_deals, status=status.HTTP_200_OK)

class BrokerViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Broker.objects.filter(is_enabled=True)
    serializer_class = serializers.BrokerSerializer
    permission_classes = (AllowAny,)
    filter_backends = [DjangoFilterBackend]
    filterset_class = BrokerFilter