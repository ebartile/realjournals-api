from pandas import DataFrame, Series
import paramiko
import time
from django.apps import apps
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
from logging import getLogger
from . import choices
from apps.settings.models import TerminalPageModule, TerminalDimensions
from apps.users.choices import CURRENCY_CHOICE, currency_codes
from . import mt5
from mt5linux import MetaTrader5
from typing import Type
from .errors import Error
from .exceptions import LoginError
from typing import Optional, Union, Tuple
from datetime import datetime, timedelta
from rest_framework import exceptions
from . import candle
from apps.utils.exceptions import WrongArguments
 
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
        "accounts.AccountRole",
        null=False,
        blank=False,
        related_name="memberships",
        on_delete=models.CASCADE,
    )
    # Invitation metadata
    email = models.EmailField(max_length=255, default=None, null=True, blank=True,
                              verbose_name=_("email"))
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
    username = models.IntegerField(default=0, unique=True)
    password = models.CharField(max_length=100, default='', blank=True, null=True)
    server = models.CharField(max_length=100, default='')
    trade_mode = models.IntegerField(choices=mt5.AccountTradeMode.choices, default=mt5.AccountTradeMode.REAL)
    balance = models.FloatField(default=0)
    leverage = models.FloatField(default=0)
    profit = models.FloatField(default=0)
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
    account_type = models.CharField(max_length=10, default="AUTO", choices=(("AUTO", "AUTO"), ("MANUAL", "MANUAL")))
    assets = models.FloatField(default=0)
    name = models.CharField(max_length=250, null=False, blank=False, verbose_name=_("name"))
    liabilities = models.FloatField(default=0)
    commission_blocked = models.FloatField(default=0)
    company = models.CharField(max_length=100, default='')
    created_date = models.DateTimeField(_("created date"), default=timezone.now)
    modified_date = models.DateTimeField( _("modified date"), auto_now=True)
    last_order_end_date = models.DateTimeField(_("last order end date"), null=True, blank=True)
    last_deal_end_date = models.DateTimeField(_("last deal end date"), null=True, blank=True)
    start_date = timezone.now() - timedelta(days=365)
    end_date = timezone.now()
    path = "/home/kasm-user/.wine/drive_c/Program Files/MetaTrader 5/terminal64.exe"
    win_percentage: float = 0.85
    timeout: int = 60000
    connected: bool
    portable: bool = False
    symbols = set()    

    slug = models.SlugField(max_length=250, unique=True, null=False, blank=True,
                            verbose_name=_("slug"))
    description = models.TextField(null=True, blank=True, verbose_name=_("description"))
    logo = models.FileField(upload_to=get_account_file_path,
                             max_length=500, null=True, blank=True,
                             verbose_name=_("logo"))
    timezone = models.CharField(max_length=63, choices=choices.TIMEZONE_CHOICES, default="UTC")
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
    has_be_configured = models.BooleanField(default=False, null=False, blank=True,
                                     verbose_name=_("has been configured"))
    is_monthly_billing = models.BooleanField(default=True, null=False, blank=True,
                                     verbose_name=_("Is Billed Monthly"))
    billing_type = models.CharField(max_length=63, choices=choices.BILLING, default="UTC")
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="accounts",
                                     through="Membership", verbose_name=_("members"),
                                     through_fields=("account", "user"))
    is_private = models.BooleanField(default=True, null=False, blank=True,
                                     verbose_name=_("is private"))
    public_permissions = ArrayField(models.TextField(choices=choices.MEMBERS_PERMISSIONS), null=True, blank=True, default=list)
    is_admin = models.BooleanField(default=False, null=False, blank=False)
    is_featured = models.BooleanField(default=False, null=False, blank=True,
                                      verbose_name=_("is featured"))
    is_system = models.BooleanField(null=False, blank=False, default=False)
    blocked_code = models.CharField(null=True, blank=True, max_length=255,
                                    choices= choices.BLOCKING_CODES + settings.EXTRA_BLOCKING_CODES,
                                    default=None, verbose_name=_("blocked code"))
    anon_permissions = ArrayField(models.TextField(choices=choices.ANON_PERMISSIONS), null=True, blank=True, default=list)
    attachments = GenericRelation("attachments.Attachment")
    creation_template = models.ForeignKey(
        "accounts.AccountTemplate",
        related_name="accounts",
        null=True,
        on_delete=models.SET_NULL,
        blank=True,
        default=None,
        verbose_name=_("creation template"))


    class Meta:
        verbose_name = "account"
        verbose_name_plural = "accounts"
        ordering = ["name", "id"]
        index_together = [
            ["name", "id"],
        ]

    def __str__(self):
        return "Account: {0} - {1}".format(self.username, self.server)

    def __repr__(self):
        return "<Account {0}>".format(self.id)

    def save(self, *args, **kwargs):
        if not self.modified_date:
            self.modified_date = timezone.now()

        if self.public_permissions is None:
            self.public_permissions = []

        if self.anon_permissions is None:
            self.anon_permissions = []

        if not bool(self.pk) and self.username and self.password and self.server:
            if not self.sign_in():
                raise exceptions.ValidationError(_("Invalid credentials"))
                    
            self.account_info()

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

    def sign_in(self) -> bool:
        """Connect to a trading account.

        Returns:
            bool: True if login was successful else False
        """
        self.connected = self.login()
        if self.connected:
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
        self.initialize()
        return self.MetaTrader5.login(self.username, password=self.password, server=self.server, timeout=self.timeout)

    def initialize(self) -> bool:
        """
        Initializes the connection to the MetaTrader terminal. All parameters are optional.

        Keyword Args:
            timeout (int): The timeout for the connection in seconds.
            portable (bool): If True, the terminal will be launched in portable mode.

        Returns:
            bool: True if successful, False otherwise.
        """
        kwargs = {key: value for key, value in (('path', self.path), ('login', self.username), ('password', self.password), ('server', self.server),
                                                ('timeout', self.timeout), ('portable', self.portable)) if value}
        try:
            self.MetaTrader5 = MetaTrader5(host = settings.MT5_HOST, port = settings.MT5_PORT )
            return self.MetaTrader5.initialize(**kwargs)
        except:
            raise Exception("Invalid login credentials")

    def last_error(self) -> list[int, str]:
        return self.MetaTrader5.last_error()

    def account_info(self) -> Optional[mt5.AccountInfo] :
        """"""
        self.initialize()
        res = self.MetaTrader5.account_info()

        if res is None:
            err = self.last_error()
            raise WrongArguments(f'Error in obtaining account information.{Error(*err)}')

        for key, value in res._asdict().items():
            if key == "login":
                setattr(self, "username", value)
            elif key == "name" and self.name:
                pass
            else:
                setattr(self, key, value)

        self.has_be_configured = True

        return res

    def symbols_get(self, group: str = "") -> Optional[list[mt5.SymbolInfo]]:
        self.initialize()
        kwargs = {'group': group} if group else {}
        res = self.MetaTrader5.symbols_get(**kwargs)

        if res is None:
            err = self.last_error()
            raise WrongArguments(f'Error in obtaining symbols.{Error(*err)}')
            return res

        return res

    def has_symbol(self, symbol: Union[str, Type[mt5.SymbolInfo]]):
        """Checks to see if a symbol is available for a trading account

        Args:
            symbol (str | SymbolInfo):

        Returns:
            bool: True if symbol is present otherwise False
        """
        try:
            self.symbol = mt5.SymbolInfo(name=str(symbol)) if not isinstance(symbol, mt5.SymbolInfo) else symbol
            return symbol in self.symbols
        except Exception as err:
            raise WrongArguments(f'Error: {err}; {symbol} not available in this market')
            return False

    def symbol_info(self, symbol: str) -> Optional[mt5.SymbolInfo]:
        self.initialize()
        self.MetaTrader5.symbol_select(symbol, True)
   
        res = self.MetaTrader5.symbol_info(symbol)

        if res is None:
            err = self.last_error()
            raise WrongArguments(f'Error in obtaining information for {symbol}.{Error(*err)}')
            return res

        return res

    def symbol_info_tick(self, symbol: str) -> Optional[mt5.Tick]:
        self.initialize()
        res = self.MetaTrader5.symbol_info_tick(symbol)

        if res is None:
            err = self.last_error()
            raise WrongArguments(f'Error in obtaining tick for {symbol}.{Error(*err)}')
            return res

        return res

    def symbol_select(self, symbol: str, enable: bool) -> bool:
        self.initialize()
        return self.MetaTrader5.symbol_select(symbol, enable)

    def market_book_add(self, symbol: str) -> bool:
        self.initialize()
        return self.MetaTrader5.market_book_add(symbol)

    def market_book_get(self, symbol: str) -> Optional[list[mt5.BookInfo]]:
        self.initialize()
        self.MetaTrader5.market_book_add(symbol)
        res = self.MetaTrader5.market_book_get(symbol)

        if res is None:
            err = self.last_error()
            raise WrongArguments(f'Error in obtaining market depth content for {symbol}.{Error(*err)}')
            return res

        return res

    def market_book_release(self, symbol: str) -> bool:
        self.initialize()
        return self.MetaTrader5.market_book_release(symbol)

    def copy_rates_from(self, symbol: str, timeframe: Union[mt5.TimeFrame, int], date_from: Union[datetime, int], count: int) -> candle.Candles:
        self.initialize()
        
        rates = self.MetaTrader5.copy_rates_from(symbol, timeframe, date_from, count)
        if rates is not None:
            return candle.Candles(data=rates)
        raise ValueError(f'Could not get rates for {symbol}')
       
       

    def copy_rates_from_pos(self, symbol: str, timeframe: Union[mt5.TimeFrame, int], start_pos: int, count: int)-> candle.Candles:
        self.initialize()
       
        rates = self.MetaTrader5.copy_rates_from_pos(symbol, timeframe, start_pos, count)
        if rates is not None:
            return candle.Candles(data=rates)
        raise ValueError(f'Could not get rates for {symbol}')
       

    def copy_rates_range(self, symbol: str, timeframe: Union[mt5.TimeFrame, int], date_from: Union[datetime, int], date_to: Union[datetime, int]) -> candle.Candles:
        self.initialize()        
        rates = self.MetaTrader5.copy_rates_range(symbol, timeframe, date_from, date_to)
        if rates is not None:
            return candle.Candles(data=rates)
        else:
            err = self.last_error()
            raise WrongArguments(f'Could not get rates for {symbol}.{Error(*err)}')
      

    def copy_ticks_from(self, symbol: str, date_from: Union[datetime, int], count: int, flags: mt5.CopyTicks):
        self.initialize()
        res = self.MetaTrader5.copy_ticks_from(symbol, date_from, count, flags)

        if res is None:
            err = self.last_error()
            raise WrongArguments(f'Error in obtaining ticks for {symbol}.{Error(*err)}')
            return res

        return res

    def copy_ticks_range(self, symbol: str, date_from: Union[datetime, int], date_to: Union[datetime, int], flags: mt5.CopyTicks):
        self.initialize()
        res = self.MetaTrader5.copy_ticks_range(symbol, date_from, date_to, flags)

        if res is None:
            err = self.last_error()
            raise WrongArguments(f'Error in obtaining ticks for {symbol}.{Error(*err)}')
            return res

        return res

    def orders_get(self, group: str = "", ticket: int = 0, symbol: str = ""):
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
        self.initialize()
        res = self.MetaTrader5.orders_get(**kwargs)

        if res is None:
            err = self.last_error()
            raise WrongArguments(f'Error in obtaining orders.{Error(*err)}')
            return res

        return res[::-1]

    def positions_get(self, group: str = "", ticket: int = 0, symbol: str = "") -> Optional[list[mt5.TradePosition]]:
        kwargs = {key: value for key, value in (('group', group), ('ticket', ticket), ('symbol', symbol)) if value}
        self.initialize()
        res = self.MetaTrader5.positions_get(**kwargs)

        if res is None:
            err = self.last_error()
            raise WrongArguments(f'Error in obtaining open positions.{Error(*err)}')
            return res

        return res[::-1]

    def history_orders_get(self, date_from: Union[datetime, int] = None, date_to: Union[datetime, int] = None, group: str = '',
                                 ticket: int = 0, position: int = 0) -> Optional[list[mt5.TradeOrder]]:
        kwargs = {key: value for key, value in (('group', group), ('ticket', ticket), ('position', position)) if value}
        self.initialize()

        if ticket:
            response = self.MetaTrader5.history_orders_get(ticket=int(ticket))
        elif position:
            response = self.MetaTrader5.history_orders_get(position=int(position))
        else:
            response = self.MetaTrader5.history_orders_get(date_from, date_to, **kwargs)

        if response is None:
            err = self.last_error()
            raise WrongArguments(f'Error in getting orders.{Error(*err)}')
            return response

        return response[::-1]

    def history_deals_get(self, date_from: Union[datetime, int] = None, date_to: Union[datetime, int] = None, group: str = '',
                                ticket: int = 0, position: int = 0) -> Optional[list[mt5.TradeDeal]]:
        kwargs = {key: value for key, value in (('group', group), ('ticket', ticket), ('position', position)) if value}

        self.initialize()
        if ticket:
            response = self.MetaTrader5.history_deals_get(ticket=int(ticket))
        elif position:
            response = self.MetaTrader5.history_deals_get(position=int(position))
        else:
            response = self.MetaTrader5.history_deals_get(date_from, date_to, **kwargs)

        if response is None:
            err = self.last_error()
            raise WrongArguments(f'Error in getting deals.{Error(*err)}')
            return response

        return response[::-1]

class Broker(models.Model):
    name = models.CharField(max_length=250, unique=True, null=False, blank=False, verbose_name=_("name"))
    description = models.TextField(null=True, blank=True, verbose_name=_("description"))
    logo = models.FileField(upload_to=get_broker_file_path,
                             max_length=500, null=True, blank=True,
                             verbose_name=_("logo"))
    auto_instructions = models.TextField(null=True, blank=True, verbose_name=_("instructions"))
    auto_video_link = models.URLField(null=True, blank=True)
    manual_instructions = models.TextField(null=True, blank=True, verbose_name=_("instructions"))
    manual_video_link = models.URLField(null=True, blank=True)
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

class AccountTemplate(models.Model):
    name = models.CharField(max_length=250, null=False, blank=False,
                            verbose_name=_("name"))
    slug = models.SlugField(max_length=250, null=False, blank=True,
                            verbose_name=_("slug"), unique=True)
    created_date = models.DateTimeField(null=False, blank=False,
                                        verbose_name=_("created date"),
                                        default=timezone.now)
    modified_date = models.DateTimeField(null=False, blank=False,
                                         verbose_name=_("modified date"))
    default_owner_role = models.CharField(max_length=50, null=False,
                                          blank=False,
                                          verbose_name=_("default owner's role"))
    page_modules = models.JSONField(null=True, blank=True, verbose_name=_("account page modules"))
    roles = models.JSONField(null=True, blank=True, verbose_name=_("roles"))

    class Meta:
        verbose_name = "account template"
        verbose_name_plural = "account templates"
        ordering = ["created_date"]

    def __str__(self):
        return self.name

    def __repr__(self):
        return "<Account Template {0}>".format(self.name)

    def save(self, *args, **kwargs):
        if not self.modified_date:
            self.modified_date = timezone.now()
        if not self.slug:
            self.slug = slugify_uniquely(self.name, self.__class__)
        super().save(*args, **kwargs)

    def load_data_from_account(self, account):

        self.page_modules = []
        for account_pages in account.account_pages.all():
            dimensions = []
            for dimension in account_pages.dimensions.all():
                dimensions.append({
                    "breakpoint": dimension.breakpoint,
                    "w": dimension.w,
                    "h": dimension.h,
                    "x": dimension.x,
                    "y": dimension.y,
                    "moved": dimension.moved,
                    "static": dimension.static,
                    "isResizable": dimension.isResizable
                })

            self.page_modules.append({
                "page": account_pages.page,
                "module": account_pages.module,
                "status": account_pages.status,
                "order": account_pages.order,
                "dimensions": dimensions
            })

        self.roles = []
        for role in account.roles.all():
            self.roles.append({
                "name": role.name,
                "slug": role.slug,
                "permissions": role.permissions,
                "order": role.order,
                "computable": role.computable
            })

        try:
            owner_membership = Membership.objects.get(account=account, user=account.owner)
            self.default_owner_role = owner_membership.role.slug
        except Membership.DoesNotExist:
            self.default_owner_role = self.roles[0].get("slug", None)

    def apply_to_account(self, account):
        AccountRole = apps.get_model("accounts", "AccountRole")

        if account.id is None:
            raise Exception("Account need an id (must be a saved account)")

        account.creation_template = self

        for page_module in self.page_modules:
            module, created = TerminalPageModule.objects.get_or_create(
                account=account,
                module=page_module['module'],
                page=page_module['page'])            
            module.status=page_module['status']
            module.order=page_module['order']
            module.save()
            
            for dimension in page_module['dimensions']:
                dimensions, created = TerminalDimensions.objects.get_or_create(
                    module=module,
                    breakpoint=dimension['breakpoint'])
                dimensions.w=dimension['w']
                dimensions.h=dimension['h']
                dimensions.x=dimension['x']
                dimensions.y=dimension['y']
                dimensions.moved=dimension['moved']
                dimensions.static=dimension['static']
                dimensions.isResizable=dimension['isResizable']
                dimensions.save()

        for role in self.roles:
            AccountRole.objects.get_or_create(
                name=role["name"],
                slug=role["slug"],
                order=role["order"],
                computable=role["computable"],
                account=account,
                permissions=role['permissions']
            )

        return account

class AccountRole(models.Model):

    account = models.ForeignKey(
        "accounts.Account",
        null=True,
        blank=False,
        related_name="roles",
        verbose_name=_("account"),
        on_delete=models.CASCADE,
    )
    name = models.CharField(max_length=200, null=False, blank=False,
                            verbose_name=_("name"))
    slug = models.SlugField(max_length=250, null=False, blank=True,
                            verbose_name=_("slug"))
    permissions = ArrayField(models.TextField(null=False, blank=False, choices=MEMBERS_PERMISSIONS),
                             null=True, blank=True, default=list, verbose_name=_("permissions"))
    order = models.IntegerField(default=10, null=False, blank=False,
                                verbose_name=_("order"))
    computable = models.BooleanField(default=True)

    class Meta:
        verbose_name = "role"
        verbose_name_plural = "roles"
        ordering = ["order", "slug"]
        unique_together = (("slug", "account"),)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify_uniquely(self.name, self.__class__)

        super().save(*args, **kwargs)

# class PaymentHistory(models.Model):
#     user=models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True)
#     account=models.ForeignKey(Account, on_delete=models.SET_NULL, blank=True, null=True)
#     created_date = models.DateTimeField(_("created date"), default=timezone.now)
#     modified_date = models.DateTimeField( _("modified date"), auto_now=True)
#     payment_status=models.BooleanField()

#     def __str__(self):
#         return self.product.name