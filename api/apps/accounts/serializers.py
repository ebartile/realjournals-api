from datetime import datetime, timezone
from rest_framework import serializers
from apps.users.serializers import UserBasicInfoSerializer
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from . import models
from .services import *
from .mt5 import DealEntry, DealType, OrderType, OrderTime, OrderFilling, OrderReason, PositionReason, DealReason, SymbolChartMode, SymbolTradeMode, SymbolSwapMode, DayOfWeek, SymbolOrderGTCMode, SymbolOptionMode, SymbolOptionRight, SymbolCalcMode, SymbolTradeExecution, OrderState
from forex_python.converter import CurrencyCodes
from apps.users.services import get_user_photo_url, get_user_big_photo_url
from apps.users.models import User
c = CurrencyCodes()

class AccountCreationSerializer(serializers.ModelSerializer):
    username = serializers.IntegerField(required=True)
    name = serializers.CharField(required=False)

    class Meta:
        model = models.Account
        fields = ("username", "name", "password", "server", "broker", "timezone", "currency", "trade_mode", "account_type", "company", "is_monthly_billing", "billing_type")

class UploadDataSerializer(serializers.ModelSerializer):
    attachment = serializers.IntegerField(required=True)

    class Meta:
        model = models.Account
        fields = ("attachment", "broker", "timezone",)

class CreateTradesSerializer(serializers.Serializer):
    history_deals = serializers.ListField(child=serializers.JSONField())
    history_orders = serializers.ListField(child=serializers.JSONField())
    orders = serializers.ListField(child=serializers.JSONField())
    positions = serializers.ListField(child=serializers.JSONField())

class BrokerSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Broker
        fields = "__all__"

class AccountSerializer(serializers.ModelSerializer):
    owner = serializers.SerializerMethodField()
    members = serializers.SerializerMethodField()
    my_permissions = serializers.SerializerMethodField()
    i_am_owner = serializers.SerializerMethodField()
    i_am_admin = serializers.SerializerMethodField()
    i_am_member = serializers.SerializerMethodField()
    logo_small_url = serializers.SerializerMethodField()
    currency_symbol = serializers.SerializerMethodField()

    class Meta:
        model = models.Account
        read_only_fields = ["id", "slug", "created_date", "modified_date", \
                            "public_permissions", "anon_permissions", "is_admin", \
                            "is_featured", "blocked_code", "logo", 
                           ]
        fields = ["id", "username", "server", "broker", "name", "slug", "description", "broker", \
                  "logo", "timezone", "created_date", "modified_date", \
                    "has_be_configured", "owner", "members", "is_private", "public_permissions", \
                    "anon_permissions", "is_admin", "is_featured", "blocked_code", "my_permissions", \
                    "i_am_owner", "i_am_member", "i_am_admin", "logo_small_url", \
                    "trade_mode", "balance", "leverage", "profit", "equity", "credit", "margin", "margin_level", "margin_free", \
                    "margin_mode", "margin_so_mode", "margin_so_call", "margin_so_so", "margin_initial", "margin_maintenance", "fifo_close", "limit_orders", \
                    "currency", "trade_allowed", "trade_expert", "currency_digits",  "currency_symbol", "assets", "liabilities", "commission_blocked", "name", "company", "created_date", \
                    "modified_date", "start_date", "end_date", "account_type", "is_monthly_billing", "billing_type"
                ]    
    
    def get_currency_symbol(self, obj):
        return c.get_symbol(obj.currency)

    def get_owner(self, obj):
        return UserBasicInfoSerializer(obj.owner).data

    def get_members(self, obj):
        assert hasattr(obj, "members_attr"), "instance must have a members_attr attribute"
        if obj.members_attr is None:
            return []

        return [m.get("id") for m in obj.members_attr if m["id"] is not None]

    def get_i_am_member(self, obj):
        assert hasattr(obj, "members_attr"), "instance must have a members_attr attribute"
        if obj.members_attr is None:
            return False

        if "request" in self.context:
            user = self.context["request"].user
            user_ids = [m.get("id") for m in obj.members_attr if m["id"] is not None]
            if not user.is_anonymous and user.id in user_ids:
                return True

        return False

    def get_my_permissions(self, obj):
        if "request" in self.context:
            user = self.context["request"].user
            return calculate_permissions(is_authenticated=user.is_authenticated,
                                         is_superuser=user.is_superuser,
                                         is_member=self.get_i_am_member(obj),
                                         is_admin=self.get_i_am_admin(obj),
                                         role_permissions=obj.my_role_permissions_attr,
                                         anon_permissions=obj.anon_permissions,
                                         public_permissions=obj.public_permissions)
        return []

    def get_i_am_owner(self, obj):
        if "request" in self.context:
            return is_account_owner(self.context["request"].user, obj)
        return False

    def get_i_am_admin(self, obj):
        if "request" in self.context:
            return is_account_admin(self.context["request"].user, obj)
        return False

    def get_logo_small_url(self, obj):
        return get_logo_small_thumbnail_url(obj)

class AccountDetailSerializer(AccountSerializer):
    total_memberships = serializers.SerializerMethodField()
    is_private_extra_info = serializers.SerializerMethodField()
    max_memberships = serializers.SerializerMethodField()
    is_out_of_owner_limits = serializers.SerializerMethodField()

    class Meta:        
        model = models.Account
        read_only_fields = AccountSerializer.Meta.read_only_fields
        fields = AccountSerializer.Meta.fields + ["total_memberships", "is_private_extra_info", "max_memberships", "is_out_of_owner_limits",]


    def to_representation(self, instance):
        for attr in ["roles_attr",]:

            assert hasattr(instance, attr), "instance must have a {} attribute".format(attr)
            val = getattr(instance, attr)
            if val is None:
                continue

            for elem in val:
                elem["name"] = _(elem["name"])

        representation = super().to_representation(instance)
        admin_fields = [
            "is_private_extra_info", "max_memberships",
        ]

        is_admin_user = False
        if "request" in self.context:
            user = self.context["request"].user
            is_admin_user = is_account_admin(user, instance)

        if not is_admin_user:
            for admin_field in admin_fields:
                del(representation[admin_field])

        return representation

    def get_total_memberships(self, obj):
        if obj.members_attr is None:
            return 0

        return len(obj.members_attr)

    def get_is_private_extra_info(self, obj):
        assert hasattr(obj, "private_accounts_same_owner_attr"), ("instance must have a private_accounts_same_"
                                                                  "owner_attr attribute")
        assert hasattr(obj, "public_accounts_same_owner_attr"), ("instance must have a public_accounts_same"
                                                                 "_owner_attr attribute")
        return check_if_account_privacy_can_be_changed(
            obj,
            current_memberships=self.get_total_memberships(obj),
            current_private_accounts=obj.private_accounts_same_owner_attr,
            current_public_accounts=obj.public_accounts_same_owner_attr
        )

    def get_max_memberships(self, obj):
        return get_max_memberships_for_account(obj)


    def get_is_out_of_owner_limits(self, obj):
        assert hasattr(obj, "private_accounts_same_owner_attr"), ("instance must have a private_accounts_same"
                                                                  "_owner_attr attribute")
        assert hasattr(obj, "public_accounts_same_owner_attr"), ("instance must have a public_accounts_same_"
                                                                 "owner_attr attribute")
        return check_if_account_is_out_of_owner_limits(
            obj,
            current_memberships=self.get_total_memberships(obj),
            current_private_accounts=obj.private_accounts_same_owner_attr,
            current_public_accounts=obj.public_accounts_same_owner_attr
        )

    def get_is_private_extra_info(self, obj):
        assert hasattr(obj, "private_accounts_same_owner_attr"), ("instance must have a private_accounts_same_"
                                                                  "owner_attr attribute")
        assert hasattr(obj, "public_accounts_same_owner_attr"), ("instance must have a public_accounts_same"
                                                                 "_owner_attr attribute")
        return check_if_account_privacy_can_be_changed(
            obj,
            current_memberships=self.get_total_memberships(obj),
            current_private_accounts=obj.private_accounts_same_owner_attr,
            current_public_accounts=obj.public_accounts_same_owner_attr
        )

class AccountExistsSerializer:
    def validate_account_id(self, value):
        if not models.Account.objects.filter(pk=value).exists():
            msg = _("There's no account with that id")
            raise ValidationError(msg)
        return value

class UpdateAccountOrderBulkSerializer(AccountExistsSerializer, serializers.Serializer):
    account_id = serializers.IntegerField()
    order = serializers.IntegerField()

    def validate(self, data):
        data = super().validate(data)
        return data


class RoleSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.AccountRole
        fields = ("id", "name", "slug", "order", "computable", "permissions",)
        read_only_fields = ("id", "slug", )
        i18n_fields = ("name",)

class SymbolInfoSerializer(serializers.Serializer):
    custom = serializers.BooleanField()
    chart_mode = serializers.CharField()
    select = serializers.BooleanField()
    visible = serializers.BooleanField()
    session_deals = serializers.IntegerField()
    session_buy_orders = serializers.IntegerField()
    session_sell_orders = serializers.IntegerField()
    volume = serializers.FloatField()
    volumehigh = serializers.FloatField()
    volumelow = serializers.FloatField()
    time = serializers.IntegerField()
    digits = serializers.IntegerField()
    spread = serializers.FloatField()
    spread_float = serializers.BooleanField()
    ticks_bookdepth = serializers.IntegerField()
    trade_calc_mode = serializers.CharField()
    trade_mode = serializers.CharField()
    start_time = serializers.IntegerField()
    expiration_time = serializers.IntegerField()
    trade_stops_level = serializers.IntegerField()
    trade_freeze_level = serializers.IntegerField()
    trade_exemode = serializers.CharField()
    swap_mode = serializers.CharField()
    swap_rollover3days = serializers.CharField()
    margin_hedged_use_leg = serializers.BooleanField()
    expiration_mode = serializers.IntegerField()
    filling_mode = serializers.IntegerField()
    order_mode = serializers.IntegerField()
    order_gtc_mode = serializers.CharField()
    option_mode = serializers.IntegerField()
    option_right = serializers.CharField()
    bid = serializers.FloatField()
    bidhigh = serializers.FloatField()
    bidlow = serializers.FloatField()
    ask = serializers.FloatField()
    askhigh = serializers.FloatField()
    asklow = serializers.FloatField()
    last = serializers.FloatField()
    lasthigh = serializers.FloatField()
    lastlow = serializers.FloatField()
    volume_real = serializers.FloatField()
    volumehigh_real = serializers.FloatField()
    volumelow_real = serializers.FloatField()
    option_strike = serializers.FloatField()
    point = serializers.FloatField()
    trade_tick_value = serializers.FloatField()
    trade_tick_value_profit = serializers.FloatField()
    trade_tick_value_loss = serializers.FloatField()
    trade_tick_size = serializers.FloatField()
    trade_contract_size = serializers.FloatField()
    trade_accrued_interest = serializers.FloatField()
    trade_face_value = serializers.FloatField()
    trade_liquidity_rate = serializers.FloatField()
    volume_min = serializers.FloatField()
    volume_max = serializers.FloatField()
    volume_step = serializers.FloatField()
    volume_limit = serializers.FloatField()
    swap_long = serializers.FloatField()
    swap_short = serializers.FloatField()
    margin_initial = serializers.FloatField()
    margin_maintenance = serializers.FloatField()
    session_volume = serializers.FloatField()
    session_turnover = serializers.FloatField()
    session_interest = serializers.FloatField()
    session_buy_orders_volume = serializers.FloatField()
    session_sell_orders_volume = serializers.FloatField()
    session_open = serializers.FloatField()
    session_close = serializers.FloatField()
    session_aw = serializers.FloatField()
    session_price_settlement = serializers.FloatField()
    session_price_limit_min = serializers.FloatField()
    session_price_limit_max = serializers.FloatField()
    margin_hedged = serializers.FloatField()
    price_change = serializers.FloatField()
    price_volatility = serializers.FloatField()
    price_theoretical = serializers.FloatField()
    price_greeks_delta = serializers.FloatField()
    price_greeks_theta = serializers.FloatField()
    price_greeks_gamma = serializers.FloatField()
    price_greeks_vega = serializers.FloatField()
    price_greeks_rho = serializers.FloatField()
    price_greeks_omega = serializers.FloatField()
    price_sensitivity = serializers.FloatField()
    basis = serializers.CharField()
    category = serializers.CharField()
    currency_base = serializers.CharField()
    currency_profit = serializers.CharField()
    currency_margin = serializers.CharField()
    bank = serializers.CharField()
    description = serializers.CharField()
    exchange = serializers.CharField()
    formula = serializers.CharField()
    isin = serializers.CharField()
    name = serializers.CharField()
    page = serializers.CharField()

    def to_representation(self, instance):
        return {
            "name": instance.name,
            "custom": instance.custom,
            "chart_mode": SymbolChartMode(instance.chart_mode).label,
            "select": instance.select,
            "visible": instance.visible,
            "session_deals": instance.session_deals,
            "session_buy_orders": instance.session_buy_orders,
            "session_sell_orders": instance.session_sell_orders,
            "volume": instance.volume,
            "volumehigh": instance.volumehigh,
            "volumelow": instance.volumelow,
            "time": instance.time,
            "digits": instance.digits,
            "spread": instance.spread,
            "spread_float": instance.spread_float,
            "ticks_bookdepth": instance.ticks_bookdepth,
            "trade_calc_mode": SymbolCalcMode(instance.trade_calc_mode).label,
            "trade_mode": SymbolTradeMode(instance.trade_mode).label,
            "start_time": instance.start_time,
            "expiration_time": instance.expiration_time,
            "trade_stops_level": instance.trade_stops_level,
            "trade_freeze_level": instance.trade_freeze_level,
            "trade_exemode": SymbolTradeExecution(instance.trade_exemode).label,
            "swap_mode": SymbolSwapMode(instance.swap_mode).label,
            "swap_rollover3days": DayOfWeek(instance.swap_rollover3days).label,
            "margin_hedged_use_leg": instance.margin_hedged_use_leg,
            "expiration_mode": instance.expiration_mode,
            "filling_mode": instance.filling_mode,
            "order_mode": instance.order_mode,
            "order_gtc_mode": SymbolOrderGTCMode(instance.order_gtc_mode).label,
            "option_mode": SymbolOptionMode(instance.option_mode).label,
            "option_right": SymbolOptionRight(instance.option_right).label,
            "bid": instance.bid,
            "bidhigh": instance.bidhigh,
            "bidlow": instance.bidlow,
            "ask": instance.ask,
            "askhigh": instance.askhigh,
            "asklow": instance.asklow,
            "last": instance.last,
            "lasthigh": instance.lasthigh,
            "lastlow": instance.lastlow,
            "volume_real": instance.volume_real,
            "volumehigh_real": instance.volumehigh_real,
            "volumelow_real": instance.volumelow_real,
            "option_strike": instance.option_strike,
            "point": instance.point,
            "trade_tick_value": instance.trade_tick_value,
            "trade_tick_value_profit": instance.trade_tick_value_profit,
            "trade_tick_value_loss": instance.trade_tick_value_loss,
            "trade_tick_size": instance.trade_tick_size,
            "trade_contract_size": instance.trade_contract_size,
            "trade_accrued_interest": instance.trade_accrued_interest,
            "trade_face_value": instance.trade_face_value,
            "trade_liquidity_rate": instance.trade_liquidity_rate,
            "volume_min": instance.volume_min,
            "volume_max": instance.volume_max,
            "volume_step": instance.volume_step,
            "volume_limit": instance.volume_limit,
            "swap_long": instance.swap_long,
            "swap_short": instance.swap_short,
            "margin_initial": instance.margin_initial,
            "margin_maintenance": instance.margin_maintenance,
            "session_volume": instance.session_volume,
            "session_turnover": instance.session_turnover,
            "session_interest": instance.session_interest,
            "session_buy_orders_volume": instance.session_buy_orders_volume,
            "session_sell_orders_volume": instance.session_sell_orders_volume,
            "session_open": instance.session_open,
            "session_close": instance.session_close,
            "session_aw": instance.session_aw,
            "session_price_settlement": instance.session_price_settlement,
            "session_price_limit_min": instance.session_price_limit_min,
            "session_price_limit_max": instance.session_price_limit_max,
            "margin_hedged": instance.margin_hedged,
            "price_change": instance.price_change,
            "price_volatility": instance.price_volatility,
            "price_theoretical": instance.price_theoretical,
            "price_greeks_delta": instance.price_greeks_delta,
            "price_greeks_theta": instance.price_greeks_theta,
            "price_greeks_gamma": instance.price_greeks_gamma,
            "price_greeks_vega": instance.price_greeks_vega,
            "price_greeks_rho": instance.price_greeks_rho,
            "price_greeks_omega": instance.price_greeks_omega,
            "price_sensitivity": instance.price_sensitivity,
            "basis": instance.basis,
            "category": instance.category,
            "currency_base": instance.currency_base,
            "currency_profit": instance.currency_profit,
            "currency_margin": instance.currency_margin,
            "bank": instance.bank,
            "description": instance.description,
            "exchange": instance.exchange,
            "formula": instance.formula,
            "isin": instance.isin,
            "page": instance.name,
        }


class BookTypeSerializer(serializers.Serializer):
    type = serializers.CharField()
    price = serializers.FloatField()
    volume = serializers.FloatField()
    volume_dbl = serializers.FloatField()


class CandleSerializer(serializers.Serializer):
    time = serializers.FloatField()
    high = serializers.FloatField()
    low = serializers.FloatField()
    close = serializers.FloatField()
    real_volume = serializers.FloatField()
    spread = serializers.FloatField()
    open = serializers.FloatField()
    tick_volume = serializers.FloatField()

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        time_integer = representation.get('time')

        if time_integer is not None:
            # Convert the integer to a datetime object
            time_datetime = datetime.fromtimestamp(time_integer, timezone.utc)
            representation['time'] = time_datetime

        return representation
  



    
    

class TicksCopySerializer(serializers.Serializer):
    ALL = 'COPY_TICKS_ALL'
    INFO = 'COPY_TICKS_INFO'
    TRADE = 'COPY_TICKS_TRADE'
    
    copy_option = serializers.ChoiceField(
        choices=(
            (ALL, 'All'),
            (INFO, 'Info'),
            (TRADE, 'Trade'),
        )
    )
        

class TradeRequestSerializer(serializers.Serializer):
    # Assuming TradeRequest is another serializer, you need to define it separately
    # You can replace 'TradeRequestSerializer' with the actual name of your TradeRequest serializer
    class TradeRequestSerializer(serializers.Serializer):
        # Define fields for the TradeRequest serializer if needed
        pass

    retcode = serializers.IntegerField()
    balance = serializers.FloatField()
    equity = serializers.FloatField()
    profit = serializers.FloatField()
    margin = serializers.FloatField()
    margin_free = serializers.FloatField()
    margin_level = serializers.FloatField()
    comment = serializers.CharField()
    request = TradeRequestSerializer()

class OrderCheckResultSerializer(serializers.Serializer):
    retcode = serializers.IntegerField()
    balance = serializers.FloatField()
    equity = serializers.FloatField()
    profit = serializers.FloatField()
    margin = serializers.FloatField()
    margin_free = serializers.FloatField()
    margin_level = serializers.FloatField()
    comment = serializers.CharField()
    request = TradeRequestSerializer()

class TradeRequestSerializer(serializers.Serializer):
    # Assuming TradeRequest is another serializer, you need to define it separately
    # You can replace 'TradeRequestSerializer' with the actual name of your TradeRequest serializer
    class TradeRequestSerializer(serializers.Serializer):
        # Define fields for the TradeRequest serializer if needed
        pass

    retcode = serializers.IntegerField()
    deal = serializers.IntegerField()
    order = serializers.IntegerField()
    volume = serializers.FloatField()
    price = serializers.FloatField()
    bid = serializers.FloatField()
    ask = serializers.FloatField()
    comment = serializers.CharField()
    request = TradeRequestSerializer()
    request_id = serializers.IntegerField()
    retcode_external = serializers.IntegerField()
    profit = serializers.FloatField()

class OrderSendResultSerializer(serializers.Serializer):
    retcode = serializers.IntegerField()
    deal = serializers.IntegerField()
    order = serializers.IntegerField()
    volume = serializers.FloatField()
    price = serializers.FloatField()
    bid = serializers.FloatField()
    ask = serializers.FloatField()
    comment = serializers.CharField()
    request = TradeRequestSerializer()
    request_id = serializers.IntegerField()
    retcode_external = serializers.IntegerField()
    profit = serializers.FloatField()

class TradePositionSerializer(serializers.Serializer):
    ticket = serializers.IntegerField()
    time = serializers.IntegerField()
    time_msc = serializers.IntegerField()
    time_update = serializers.IntegerField()
    time_update_msc = serializers.IntegerField()
    type = serializers.CharField()
    magic = serializers.FloatField()
    identifier = serializers.IntegerField()
    reason = serializers.CharField()
    volume = serializers.FloatField()
    price_open = serializers.FloatField()
    sl = serializers.FloatField()
    tp = serializers.FloatField()
    price_current = serializers.FloatField()
    swap = serializers.FloatField()
    profit = serializers.FloatField()
    symbol = serializers.CharField()
    comment = serializers.CharField()
    external_id = serializers.CharField()

    def to_representation(self, instance):
        return {
            "ticket": instance.ticket,
            'time': datetime.fromtimestamp(instance.time, timezone.utc),
            'time_update': datetime.fromtimestamp(instance.time_update, timezone.utc),
            'type': OrderType(instance.type).label,
            'magic': instance.magic,
            'identifier': instance.identifier,
            "reason": PositionReason(instance.reason).label,
            'volume': instance.volume,
            'price_open': instance.price_open,
            'sl': instance.sl,
            'tp': instance.tp,
            'price_current': instance.price_current,
            'swap': instance.swap,
            'profit': instance.profit,
            'symbol': instance.symbol,
            'comment': instance.comment,
            'external_id': instance.external_id
        }

class OrdersSerializer(serializers.Serializer):
    ticket = serializers.IntegerField()
    time_setup = serializers.IntegerField()
    time_setup_msc = serializers.IntegerField()
    time_expiration = serializers.IntegerField()
    time_done = serializers.IntegerField()
    time_done_msc = serializers.IntegerField()
    type = serializers.CharField()
    type_time = serializers.CharField()
    type_filling = serializers.CharField()
    state = serializers.IntegerField()
    magic = serializers.IntegerField()
    position_id = serializers.IntegerField()
    position_by_id = serializers.IntegerField()
    reason = serializers.CharField()
    volume_current = serializers.FloatField()
    volume_initial = serializers.FloatField()
    price_open = serializers.FloatField()
    sl = serializers.FloatField()
    tp = serializers.FloatField()
    price_current = serializers.FloatField()
    price_stoplimit = serializers.FloatField()
    symbol = serializers.CharField()
    comment = serializers.CharField()
    external_id = serializers.CharField()

    def to_representation(self, instance):
        return {
            'ticket': instance.ticket,
            'time': datetime.fromtimestamp(instance.time_setup, timezone.utc),
            'time_done': datetime.fromtimestamp(instance.time_done, timezone.utc),
            'type': OrderType(instance.type).label,
            'type_time': OrderTime(instance.type_time).label,
            'type_filling': OrderFilling(instance.type_filling).label,
            'state': OrderState(instance.state).label,
            'magic': instance.magic,
            'position_id': instance.position_id,
            'position_by_id': instance.position_by_id,
            'reason': OrderReason(instance.reason).label,
            'volume_current': instance.volume_current,
            'volume_initial': instance.volume_initial,
            'price_open': instance.price_open,
            'sl': instance.sl,
            'tp': instance.tp,
            'price_current': instance.price_current,
            'price_stoplimit': instance.price_stoplimit,
            'symbol': instance.symbol,
            'comment': instance.comment,
            'external_id': instance.external_id
        }

        
class HistoryDealsSerializer(serializers.Serializer):
    ticket = serializers.IntegerField()
    order = serializers.IntegerField()
    time = serializers.IntegerField()
    time_msc = serializers.IntegerField()
    type = serializers.IntegerField()
    entry = serializers.IntegerField()
    magic = serializers.IntegerField()
    position_id = serializers.IntegerField()
    reason = serializers.CharField()
    volume = serializers.FloatField()
    price = serializers.FloatField()
    commission = serializers.FloatField()
    swap = serializers.FloatField()
    profit = serializers.FloatField()
    fee = serializers.FloatField()
    symbol = serializers.CharField()
    comment = serializers.CharField()
    external_id = serializers.CharField()

    def to_representation(self, instance):
        return {
            'ticket': instance.ticket,
            'order': instance.order,
            'time': datetime.fromtimestamp(instance.time, timezone.utc),
            'type': DealType(instance.type).label,
            'entry': DealEntry(instance.entry).label,
            'magic': instance.magic,
            'position_id': instance.position_id,
            "reason": DealReason(instance.reason).label,
            'volume': instance.volume,
            'price': instance.price,
            'commission': instance.commission,
            'swap': instance.swap,            
            'profit': instance.profit,
            'fee': instance.fee,
            'symbol': instance.symbol,
            'comment': instance.comment,
            'external_id': instance.external_id
        }

class MembershipSerializer(serializers.ModelSerializer):
    role_name = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()
    is_user_active = serializers.SerializerMethodField()
    photo = serializers.SerializerMethodField()
    account_name = serializers.SerializerMethodField()
    account_slug = serializers.SerializerMethodField()
    invited_by = UserBasicInfoSerializer()
    is_owner = serializers.SerializerMethodField()
    role = RoleSerializer()
    user = UserBasicInfoSerializer()

    class Meta:
        model = models.Membership
        read_only_fields = ["id", "account", \
                            "is_admin", "created_at", "user", \
                            "invitation_extra_text", "user_order", "role_name", \
                            "full_name", "is_user_active", "photo", \
                            "account_name", "account_slug", "invited_by", "is_owner" \
                           ]
        fields = '__all__' 

    def get_role_name(self, obj):
        return obj.role.name if obj.role else None

    def get_full_name(self, obj):
        return obj.user.get_full_name() if obj.user else None

    def get_is_user_active(self, obj):
        return obj.user.is_active if obj.user else False

    def get_color(self, obj):
        return obj.user.color if obj.user else None

    def get_photo(self, obj):
        return get_user_photo_url(obj.user)

    def get_gravatar_id(self, obj):
        return get_user_gravatar_id(obj.user)

    def get_account_name(self, obj):
        return obj.account.name if obj and obj.account else ""

    def get_account_slug(self, obj):
        return obj.account.slug if obj and obj.account else ""

    def get_is_owner(self, obj):
        return (obj and obj.user_id and obj.account_id and obj.account.owner_id and
                obj.user_id == obj.account.owner_id)

class MembershipCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Membership
        fields = ('email', 'role', 'invitation_extra_text') 

    def validate_email(self, value):
        email = value
        user = User.objects.filter(Q(email=email)).first()
        if user is not None:
            email = user.email
            self.user = user
        else:
            email = email
            self.user = None

        self.email = email
        return value

class MembershipAdminSerializer(MembershipSerializer):
    email = serializers.CharField()
    user_email = serializers.SerializerMethodField()

    def get_user_email(self, obj):
        return obj.user.email if obj.user else None
