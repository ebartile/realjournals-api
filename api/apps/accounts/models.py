import paramiko
import time
from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.utils.files import get_file_path
from django.utils import timezone
from django.conf import settings
from django.core.exceptions import ValidationError
from .choices import MEMBERS_PERMISSIONS, ANON_PERMISSIONS
from django.contrib.postgres.fields import ArrayField
from apps.utils.slug import slugify_uniquely
from apps.utils.slug import slugify_uniquely_for_queryset
from django_pglocks import advisory_lock
from dateutil.relativedelta import relativedelta
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.auth import get_user_model
from apps.utils.time import timestamp_ms
from datetime import datetime
from logging import getLogger
from typing import Type
from . import choices
from . import mt5
from .errors import Error
from .exceptions import LoginError

logger = getLogger()

def get_account_file_path(instance, filename):
    return get_file_path(instance, filename, "account")

def get_broker_file_path(instance, filename):
    return get_file_path(instance, filename, "broker")

class Membership(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        default=None,
        related_name="memberships",
        on_delete=models.CASCADE,
    )
    account = models.ForeignKey(
        "Account",
        null=False,
        blank=False,
        related_name="memberships",
        on_delete=models.CASCADE,
    )
    role = models.ForeignKey(
        "users.Role",
        null=False,
        blank=False,
        related_name="memberships",
        on_delete=models.CASCADE,
    )
    created_at = models.DateTimeField(default=timezone.now,
                                      verbose_name=_("create at"))
    token = models.CharField(max_length=60, blank=True, null=True, default=None,
                             verbose_name=_("token"))

    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="ihaveinvited+",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    invitation_extra_text = models.TextField(null=True, blank=True,
                                             verbose_name=_("invitation extra text"))
    is_admin = models.BooleanField(default=False, null=False, blank=False)
    user_order = models.BigIntegerField(default=timestamp_ms, null=False, blank=False,
                                        verbose_name=_("user order"))

    class Meta:
        verbose_name = "membership"
        verbose_name_plural = "memberships"
        unique_together = ("user", "account",)
        ordering = ["account", "user__first_name", "user__last_name", "user__email",]

    def get_related_people(self):
        related_people = get_user_model().objects.filter(id=self.user.id)
        return related_people

    def clean(self):
        # TODO: Review and do it more robust
        memberships = Membership.objects.filter(user=self.user, account=self.account)
        if self.user and memberships.count() > 0 and memberships[0].id != self.id:
            raise ValidationError(_('The user is already member of the account'))

class Account(models.Model):
    name = models.CharField(max_length=250, null=False, blank=False, verbose_name=_("name"))
    slug = models.SlugField(max_length=250, unique=True, null=False, blank=True,
                            verbose_name=_("slug"))
    description = models.TextField(null=False, blank=False, verbose_name=_("description"))
    logo = models.FileField(upload_to=get_account_file_path,
                             max_length=500, null=True, blank=True,
                             verbose_name=_("logo"))
    created_date = models.DateTimeField(_("created date"), default=timezone.now)
    modified_date = models.DateTimeField( _("modified date"), auto_now=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        related_name="owned_accounts",
        verbose_name=_("owner"),
        on_delete=models.SET_NULL,
    )
    broker = models.ForeignKey(
        "accounts.Broker",
        null=True,
        blank=True,
        related_name="broker",
        verbose_name=_("broker"),
        on_delete=models.SET_NULL,
    )
    timezone = models.CharField(max_length=63, choices=choices.TIMEZONE_CHOICES)
    has_be_configured = models.BooleanField(default=False, null=False, blank=True,
                                     verbose_name=_("has been configured"))
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="accounts",
                                     through="Membership", verbose_name=_("members"),
                                     through_fields=("account", "user"))
    is_private = models.BooleanField(default=True, null=False, blank=True,
                                     verbose_name=_("is private"))
    public_permissions = ArrayField(models.TextField(null=False, blank=False, choices=choices.MEMBERS_PERMISSIONS, default=[]))
    is_admin = models.BooleanField(default=False, null=False, blank=False)
    is_featured = models.BooleanField(default=False, null=False, blank=True,
                                      verbose_name=_("is featured"))
    is_system = models.BooleanField(null=False, blank=False, default=False)
    blocked_code = models.CharField(null=True, blank=True, max_length=255,
                                    choices= choices.BLOCKING_CODES + settings.EXTRA_BLOCKING_CODES,
                                    default=None, verbose_name=_("blocked code"))
    anon_permissions = ArrayField(models.TextField(null=False, blank=False, choices=choices.ANON_PERMISSIONS),
                                  null=True, blank=True, default=list, verbose_name=_("anonymous permissions"))
    attachments = GenericRelation("attachments.Attachment")
    username = models.IntegerField(default=0)
    password = models.CharField(max_length=100, default='')
    server = models.CharField(max_length=100, default='')
    trade_mode = models.IntegerField(choices=mt5.AccountTradeMode.choices, default=mt5.AccountTradeMode.REAL)
    balance = models.FloatField(default=0)
    leverage = models.FloatField(default=0)
    profit = models.FloatField(default=0)
    point = models.FloatField(default=0)
    amount = models.FloatField(default=0)
    equity = models.FloatField(default=0)
    credit = models.FloatField(default=0)
    margin = models.FloatField(default=0)
    margin_level = models.FloatField(default=0)
    margin_free = models.FloatField(default=0)
    margin_mode = models.IntegerField(choices=mt5.AccountMarginMode.choices, default=mt5.AccountMarginMode.EXCHANGE)
    margin_so_mode = models.IntegerField(choices=mt5.AccountStopOutMode.choices, default=mt5.AccountStopOutMode.MONEY)
    margin_so_call = models.FloatField(default=0)
    margin_so_so = models.FloatField(default=0)
    margin_initial = models.FloatField(default=0)
    margin_maintenance = models.FloatField(default=0)
    fifo_close = models.BooleanField(default=0)
    limit_orders = models.FloatField(default=0)
    currency = models.CharField(max_length=10, default="USD")
    trade_allowed = models.BooleanField(default=True)
    trade_expert = models.BooleanField(default=True)
    currency_digits = models.IntegerField(default=0)
    assets = models.FloatField(default=0)
    liabilities = models.FloatField(default=0)
    commission_blocked = models.FloatField(default=0)
    name = models.CharField(max_length=100)
    company = models.CharField(max_length=100)

    win_percentage: float = 0.85
    timeout: int = 60000
    connected: bool
    portable: bool = False
    symbols = set()

    class Meta:
        verbose_name = "account"
        verbose_name_plural = "accounts"
        ordering = ["name", "id"]
        index_together = [
            ["name", "id"],
        ]

    def __str__(self):
        return self.name

    def __repr__(self):
        return "<Account {0}>".format(self.id)

    def save(self, *args, **kwargs):
        if not self.modified_date:
            self.modified_date = timezone.now()

        if self.public_permissions is None:
            self.public_permissions = []

        if self.anon_permissions is None:
            self.anon_permissions = []

        if not self.slug:
            with advisory_lock("account-creation"):
                base_slug = self.name
                if settings.DEFAULT_ACCOUNT_SLUG_PREFIX:
                    base_slug = "{}-{}".format(self.owner.username, self.name)
                self.slug = slugify_uniquely(base_slug, self.__class__)
                super().save(*args, **kwargs)
        else:
            super().save(*args, **kwargs)

    @property
    def account(self):
        return self

    def refresh(self):
        """
        Refreshes the account instance with the latest account details from the MetaTrader 5 terminal
        """
        account_info = self.account_info()
        for key, value in account_info._asdict().items():
            setattr(self, key, value)
        self.save()


    def sign_in(self) -> bool:
        """Connect to a trading account.

        Returns:
            bool: True if login was successful else False
        """
        self.initialize()
        self.connected = self.login()
        if self.connected:
            self.symbols = self.symbols_get()
            return self.connected
        return False

    def login(self) -> bool:
        """
        Connects to the MetaTrader terminal using the specified login, password and server.

        Args:
            login (int): The trading account number.
            password (str): The trading account password.
            server (str): The trading server name.
            timeout (int): The timeout for the connection in seconds.

        Returns:
            bool: True if successful, False otherwise.
        """
        return self._login(self.username, password=self.password, server=self.server, timeout=self.timeout)

    def initialize(self) -> bool:
        """
        Initializes the connection to the MetaTrader terminal. All parameters are optional.

        Keyword Args:
            timeout (int): The timeout for the connection in seconds.
            portable (bool): If True, the terminal will be launched in portable mode.

        Returns:
            bool: True if successful, False otherwise.
        """
        kwargs = {key: value for key, value in (('login', self.username), ('password', self.password), ('server', self.server),
                                                ('timeout', self.timeout), ('portable', self.portable), ('path', self.path)) if value}
        return self._initialize(**kwargs)

    def last_error(self) -> tuple[int, str]:
        return self._last_error()

    def version(self) -> tuple[int, int, str] | None:
        """"""
        res = self._version()
        if res is None:
            err = self.last_error()
            logger.warning(f'Error in obtaining version information.{Error(*err)}')
        return res

    def account_info(self) -> mt5.AccountInfo | None:
        """"""
        res = self._account_info()

        if res is None:
            err = self.last_error()
            logger.warning(f'Error in obtaining account information.{Error(*err)}')

        return res

    def terminal_info(self) -> mt5.TerminalInfo | None:
        res = self._terminal_info()

        if res is None:
            err = self.last_error()
            logger.warning(f'Error in obtaining terminal information.{Error(*err)}')
            return res

        return res

    def symbols_total(self) -> int:
        return self._symbols_total()

    def symbols_get(self, group: str = "") -> tuple[mt5.SymbolInfo] | None:
        kwargs = {'group': group} if group else {}
        res = self._symbols_get(**kwargs)

        if res is None:
            err = self.last_error()
            logger.warning(f'Error in obtaining symbols.{Error(*err)}')
            return res

        return res

    def has_symbol(self, symbol: str | Type[mt5.SymbolInfo]):
        """Checks to see if a symbol is available for a trading account

        Args:
            symbol (str | SymbolInfo):

        Returns:
            bool: True if symbol is present otherwise False
        """
        try:
            symbol = mt5.SymbolInfo(name=str(symbol)) if not isinstance(symbol, mt5.SymbolInfo) else symbol
            return symbol in self.symbols
        except Exception as err:
            logger.warning(f'Error: {err}; {symbol} not available in this market')
            return False

    def symbol_info(self, symbol: str) -> mt5.SymbolInfo | None:
        res = self._symbol_info(symbol)

        if res is None:
            err = self.last_error()
            logger.warning(f'Error in obtaining information for {symbol}.{Error(*err)}')
            return res

        return res

    def symbol_info_tick(self, symbol: str) -> mt5.Tick | None:
        res = self._symbol_info_tick(symbol)

        if res is None:
            err = self.last_error()
            logger.warning(f'Error in obtaining tick for {symbol}.{Error(*err)}')
            return res

        return res

    def symbol_select(self, symbol: str, enable: bool) -> bool:
        return self._symbol_select(symbol, enable)

    def market_book_add(self, symbol: str) -> bool:
        return self._market_book_add(symbol)

    def market_book_get(self, symbol: str) -> tuple[mt5.BookInfo] | None:
        res = self._market_book_get(symbol)

        if res is None:
            err = self.last_error()
            logger.warning(f'Error in obtaining market depth content for {symbol}.{Error(*err)}')
            return res

        return res

    def market_book_release(self, symbol: str) -> bool:
        return self._market_book_release(symbol)

    def copy_rates_from(self, symbol: str, timeframe: mt5.TimeFrame, date_from: datetime | int, count: int):
        res = self._copy_rates_from(symbol, timeframe, date_from, count)

        if res is None:
            err = self.last_error()
            logger.warning(f'Error in obtaining rates for {symbol}.{Error(*err)}')
            return res

        return res

    def copy_rates_from_pos(self, symbol: str, timeframe: mt5.TimeFrame, start_pos: int, count: int):
        res = self._copy_rates_from_pos(symbol, timeframe, start_pos, count)

        if res is None:
            err = self.last_error()
            logger.warning(f'Error in obtaining rates for {symbol}.{Error(*err)}')
            return res

        return res

    def copy_rates_range(self, symbol: str, timeframe: mt5.TimeFrame, date_from: datetime | int,
                               date_to: datetime | int):
        res = self._copy_rates_range(symbol, timeframe, date_from, date_to)

        if res is None:
            err = self.last_error()
            logger.warning(f'Error in obtaining rates for {symbol}.{Error(*err)}')
            return res

        return res

    def copy_ticks_from(self, symbol: str, date_from: datetime | int, count: int, flags: mt5.CopyTicks):
        res = self._copy_ticks_from(symbol, date_from, count, flags)

        if res is None:
            err = self.last_error()
            logger.warning(f'Error in obtaining ticks for {symbol}.{Error(*err)}')
            return res

        return res

    def copy_ticks_range(self, symbol: str, date_from: datetime | int, date_to: datetime | int, flags: mt5.CopyTicks):
        res = self._copy_ticks_range(symbol, date_from, date_to, flags)

        if res is None:
            err = self.last_error()
            logger.warning(f'Error in obtaining ticks for {symbol}.{Error(*err)}')
            return res

        return res

    def orders_total(self) -> int:
        return self._orders_total()

    def orders_get(self, group: str = "", ticket: int = 0, symbol: str = "") -> tuple[mt5.TradeOrder] | None:
        """Get active orders with the ability to filter by symbol or ticket. There are three call options.
           Call without parameters. Return active orders on all symbols

        Keyword Args:
            symbol (str): Symbol name. Optional named parameter. If a symbol is specified, the ticket parameter is ignored.

            group (str): The filter for arranging a group of necessary symbols. Optional named parameter. If the group is specified, the function
                returns only active orders meeting a specified criteria for a symbol name.

            ticket (int): Order ticket (ORDER_TICKET). Optional named parameter.

        Returns:
            list[TradeOrder]: A list of active trade orders as TradeOrder objects
        """
        kwargs = {key: value for key, value in (('group', group), ('ticket', ticket), ('symbol', symbol)) if value}
        res = self._orders_get(**kwargs)

        if res is None:
            err = self.last_error()
            logger.warning(f'Error in obtaining orders.{Error(*err)}')
            return res

        return res

    def order_calc_margin(self, action: mt5.OrderType, symbol: str, volume: float, price: float) -> float | None:
        res = self._order_calc_margin(action, symbol, volume, price)

        if res is None:
            err = self.last_error()
            logger.warning(f'Error in calculating margin.{Error(*err)}')
            return res

        return res

    def order_calc_profit(self, action: mt5.OrderType, symbol: str, volume: float, price_open: float,
                                price_close: float) -> float | None:
        res = self._order_calc_profit(action, symbol, volume, price_open, price_close)

        if res is None:
            err = self.last_error()
            logger.warning(f'Error in calculating profit.{Error(*err)}')
            return res

        return res

    def order_check(self, request: dict) -> mt5.OrderCheckResult:
        return self._order_check(request)

    def order_send(self, request: dict) -> mt5.OrderSendResult:
        return self._order_send(request)

    def positions_total(self) -> int:
        return self._positions_total()

    def positions_get(self, group: str = "", ticket: int = 0, symbol: str = "") -> tuple[mt5.TradePosition] | None:
        kwargs = {key: value for key, value in (('group', group), ('ticket', ticket), ('symbol', symbol)) if value}
        res = self._positions_get(**kwargs)

        if res is None:
            err = self.last_error()
            logger.warning(f'Error in obtaining open positions.{Error(*err)}')
            return res

        return res

    def history_orders_total(self, date_from: datetime | int, date_to: datetime | int) -> int:
        return self._history_orders_total(date_from, date_to)

    def history_orders_get(self, date_from: datetime | int = None, date_to: datetime | int = None, group: str = '',
                                 ticket: int = 0, position: int = 0) -> tuple[mt5.TradeOrder] | None:
        kwargs = {key: value for key, value in (('date_from', date_from), ('date_to', date_to), ('group', group),
                                                ('ticket', ticket), ('position', position)) if value}
        res = self._history_orders_get(**kwargs)

        if res is None:
            err = self.last_error()
            logger.warning(f'Error in getting orders.{Error(*err)}')
            return res

        return res

    def history_deals_total(self, date_from: datetime | int, date_to: datetime | int) -> int:
        return self._history_deals_total(date_from, date_to)

    def history_deals_get(self, date_from: datetime | int = None, date_to: datetime | int = None, group: str = '',
                                ticket: int = 0, position: int = 0) -> tuple[mt5.TradeDeal] | None:
        kwargs = {key: value for key, value in (('date_from', date_from), ('date_to', date_to), ('group', group),
                                                ('ticket', ticket), ('position', position)) if value}
        res = self._history_deals_get(**kwargs)
        if res is None:
            err = self.last_error()
            logger.warning(f'Error in getting deals.{Error(*err)}')
            return res

        return res


class Broker(models.Model):
    name = models.CharField(max_length=250, unique=True, null=False, blank=False, verbose_name=_("name"))
    description = models.TextField(null=True, blank=True, verbose_name=_("description"))
    logo = models.FileField(upload_to=get_broker_file_path,
                             max_length=500, null=True, blank=True,
                             verbose_name=_("logo"))
    supports_stocks = models.BooleanField(default=False, null=False, blank=False)
    supports_options = models.BooleanField(default=False, null=False, blank=False)
    supports_forex = models.BooleanField(default=False, null=False, blank=False)
    supports_futures = models.BooleanField(default=False, null=False, blank=False)
    supports_crypto = models.BooleanField(default=False, null=False, blank=False)
    supports_metatrader_4 = models.BooleanField(default=False, null=False, blank=False)
    supports_metatrader_5 = models.BooleanField(default=False, null=False, blank=False)
    supports_file_import = models.BooleanField(default=False, null=False, blank=False)
    supports_auto_sync_import = models.BooleanField(default=False, null=False, blank=False)
    is_enabled = models.BooleanField(default=False, null=False, blank=False)
    created_date = models.DateTimeField(_("created date"), default=timezone.now)

    class Meta:
        verbose_name = "broker"
        verbose_name_plural = "brokers"

    def __str__(self):
        return self.name

