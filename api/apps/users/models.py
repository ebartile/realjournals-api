import uuid
import re
from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, UserManager
from django.utils.translation import gettext_lazy as _
from django.core import validators
from apps.utils.files import get_file_path
from django.utils import timezone
from .tokens import get_token_for_user
from django.contrib.postgres.fields import ArrayField
from apps.utils.slug import slugify_uniquely
from apps.accounts.choices import BLOCKED_BY_OWNER_LEAVING
from django_otp.plugins.otp_totp.models import TOTPDevice
from apps.utils.time import timestamp_ms
from apps.accounts import services as account_services
from django_pglocks import advisory_lock
import pycountry
from .choices import *

def get_default_uuid():
    return uuid.uuid4().hex

def get_user_file_path(instance, filename):
    return get_file_path(instance, filename, "user")

class User(AbstractBaseUser):
    uuid = models.CharField(max_length=32, editable=False, null=False,
                            blank=False, unique=True, default=get_default_uuid)
    username = models.CharField(_("username"), max_length=255, unique=True,
        help_text=_("Required. 30 characters or fewer. Letters, numbers and "
                    "/./-/_ characters"), default=get_default_uuid)
    email = models.EmailField(_("email address"), max_length=255, null=False, blank=False, unique=True)
    is_active = models.BooleanField(_("active"), default=True,
        help_text=_("Designates whether this user should be treated as "
                    "active. Unselect this instead of deleting accounts."))
    is_superuser = models.BooleanField(_("superuser status"), default=False,
        help_text=_("Designates that this user has all permissions without "
                    "explicitly assigning them."))
    is_staff = models.BooleanField(_('staff status'), default=False,
        help_text=_('Designates whether the user can log into this admin site.'),
    )
    first_name = models.CharField(_("first name"), max_length=256, blank=True)
    last_name = models.CharField(_("last name"), max_length=256, blank=True)
    bio = models.TextField(null=False, blank=True, default="", verbose_name=_("biography"))
    photo = models.FileField(upload_to=get_user_file_path,
                             max_length=500, null=True, blank=True,
                             verbose_name=_("photo"))
    last_login = models.DateTimeField(_("last login"), null=True, blank=True)
    last_seen = models.DateTimeField(_("last seen"), null=True, blank=True)
    date_of_birth = models.DateTimeField(_("date of birth"), null=True, blank=True)
    email_verified_at = models.DateTimeField(_("email verified at"), null=True, blank=True)
    date_joined = models.DateTimeField(_("date joined"), default=timezone.now)
    updated_at = models.DateTimeField( _("updated date"), auto_now=True)
    accepted_terms = models.BooleanField(_("accepted terms"), default=False)
    read_new_terms = models.BooleanField(_("new terms read"), default=False)
    lang = models.CharField(max_length=20, null=True, blank=True, default="en",
                            verbose_name=_("default language"), choices=settings.LANGUAGES)
    timezone = models.CharField(max_length=63, null=True, blank=True, default="GMT",
                                verbose_name=_("default timezone"), choices=TIMEZONE_CHOICES)
    token = models.CharField(max_length=200, null=True, blank=True, default=None,
                             verbose_name=_("token"))
    email_token = models.CharField(max_length=200, null=True, blank=True, default=None,
                         verbose_name=_("email token"))
    postal_code = models.CharField(max_length=20, verbose_name=_("post code"), null=True, blank=True)
    # TODO: two factor
    two_factor_enabled = models.BooleanField(default=False, verbose_name=_("two factor enabled"))
    followable = models.BooleanField(default=True, verbose_name=_("is followable"))
    state = models.CharField(max_length=50, verbose_name=_("state"), null=True, blank=True)  # Adjust max_length as needed
    city = models.CharField(max_length=100, verbose_name=_("city"), null=True, blank=True, default="",)  # Adjust max_length as needed
    country = models.CharField(max_length=3, verbose_name=_("country"), choices=ISO_CODE_CHOICES, null=True, blank=True, default="US")  # Adjust max_length as needed
    new_email = models.EmailField(_("new email address"), null=True, blank=True)
    presence = models.CharField(max_length=15, choices=PRESENCE_CHOICE, null=True, blank=True, default="offline")
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICE, null=True, blank=True, default="USD")
    continent = models.CharField(max_length=2, choices=CONTINENT_CHOICES, null=True, blank=True, default="AF")
    verified_email = models.BooleanField(null=False, blank=False, default=False)
    is_system = models.BooleanField(null=False, blank=False, default=False)
    registered_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    location = models.JSONField(null=True, blank=True, default=None)
    max_private_accounts = models.IntegerField(null=True, blank=True,
                                               default=settings.MAX_PRIVATE_ACCOUNTS_PER_USER,
                                               verbose_name=_("max number of owned private accounts"))
    max_public_accounts = models.IntegerField(null=True, blank=True,
                                              default=settings.MAX_PUBLIC_ACCOUNTS_PER_USER,
                                              verbose_name=_("max number of owned public accounts"))
    max_memberships_private_accounts = models.IntegerField(null=True, blank=True,
                                                           default=settings.MAX_MEMBERSHIPS_PRIVATE_ACCOUNT,
                                                           verbose_name=_("max number of memberships for "
                                                                          "each owned private accounts"))
    max_memberships_public_accounts = models.IntegerField(null=True, blank=True,
                                                          default=settings.MAX_MEMBERSHIPS_PUBLIC_ACCOUNT,
                                                          verbose_name=_("max number of memberships for "
                                                                         "each owned public accounts"))

    _cached_memberships = None
    _cached_notify_levels = None

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    objects = UserManager()

    class Meta:
        verbose_name = "user"
        verbose_name_plural = "users"
        ordering = ["username"]

    def __str__(self):
        return self.get_full_name()

    def has_perm(self, perm, obj=None):
        """
        Returns True if the user is superadmin and is active
        """
        return self.is_active and self.is_superuser

    def has_perms(self, perm_list, obj=None):
        """
        Returns True if the user is superadmin and is active
        """
        return self.is_active and self.is_superuser

    def has_module_perms(self, app_label):
        """
        Returns True if the user is superadmin and is active
        """
        return self.is_active and self.is_superuser

    def get_full_name(self):
        return "".join([self.first_name, " ", self.last_name]) or self.username or self.email

    def get_short_name(self):
        "Returns the short name for the user."
        return self.first_name or self.username

    def get_country_name(self):
        try:
            country = pycountry.countries.get(alpha_2=self.country)
            return country.name
        except pycountry.db.DataError:
            return None

    def get_currency_name(self):
        try:
            return currency_codes.get_currency_name(self.currency)
        except StopIteration:
            return None
        
    def get_continent_name(self):
        for continent_code, continent_name in CONTINENT_CHOICES:
            if continent_code == self.continent:
                return continent_name
        return None
    
    def save(self, *args, **kwargs):
        get_token_for_user(self, "cancel_account")
        super().save(*args, **kwargs)
    
    def cancel(self):
        with advisory_lock("delete-user"):
            deleted_user_prefix = "deleted-user-{}".format(timestamp_ms())
            self.email = "{}@realjournals.com".format(self.username)
            self.is_active = False
            self.token = None
            self.set_unusable_password()
            self.save()
   
        # Blocking all owned accounts
        self.owned_accounts.update(blocked_code=BLOCKED_BY_OWNER_LEAVING)

        # Remove all memberships
        self.memberships.all().delete()

    def contacts_visible_by_user(self, user):
        qs = User.objects.filter(is_active=True)
        account_ids = account_services.get_visible_account_ids(self, user)
        qs = qs.filter(memberships__account_id__in=account_ids)
        qs = qs.exclude(id=self.id)
        return qs

    def _fill_cached_memberships(self):
        self._cached_memberships = {}
        qs = self.memberships.select_related("user", "account", "role")
        for membership in qs.all():
            self._cached_memberships[membership.account.id] = membership

    @property
    def cached_memberships(self):
        if self._cached_memberships is None:
            self._fill_cached_memberships()

        return self._cached_memberships.values()


    def cached_membership_for_account(self, account):
        if self._cached_memberships is None:
            self._fill_cached_memberships()

        return self._cached_memberships.get(account.id, None)

MEMBERS_PERMISSIONS = [
    ('view_account', _('View account')),
]

class Role(models.Model):
    name = models.CharField(max_length=200, null=False, blank=False,
                            verbose_name=_("name"))
    slug = models.SlugField(max_length=250, null=False, blank=True,
                            verbose_name=_("slug"), unique=True)
    permissions = ArrayField(models.TextField(null=False, blank=False, choices=MEMBERS_PERMISSIONS),
                             null=True, blank=True, default=list, verbose_name=_("permissions"))
    order = models.IntegerField(default=10, null=False, blank=False,
                                verbose_name=_("order"))
    computable = models.BooleanField(default=True)

    class Meta:
        verbose_name = "role"
        verbose_name_plural = "roles"
        ordering = ["order", "slug"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify_uniquely(self.name, self.__class__)

        super().save(*args, **kwargs)
    
