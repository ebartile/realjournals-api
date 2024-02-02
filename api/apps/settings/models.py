from django.conf import settings

from django.db import models
from django.utils import timezone

from .choices import ADMIN_PAGE_CHOICES, TERMINAL_PAGE_CHOICES, TERMINAL_MODULES_CHOICES, ADMIN_MODULES_CHOICES
from django.contrib.postgres.fields import ArrayField
from django.utils.translation import gettext_lazy as _
from django.core.validators import MaxValueValidator, MinValueValidator

class TerminalPageModule(models.Model):
    account = models.ForeignKey("accounts.Account", null=True, related_name="account_pages", on_delete=models.CASCADE)
    page = models.CharField(max_length=255, choices=TERMINAL_PAGE_CHOICES, default="terminal.dashboard")
    module = models.CharField(max_length=255, choices=TERMINAL_MODULES_CHOICES, default="net_profit_loss")
    status = models.BooleanField(default=True)
    order = models.IntegerField(default=0, null=False, blank=False, verbose_name=_("order"))
    created_at = models.DateTimeField(default=timezone.now, verbose_name=_("create at"))
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("account", "page", "module")
        ordering = ('order',)

    def __str__(self):
        return f"{self.page} - {self.module}"

class AdminPageModule(models.Model):
    user = models.ForeignKey("users.User", null=True, related_name="user_admin_pages", on_delete=models.CASCADE)
    page = models.CharField(max_length=255, choices=ADMIN_PAGE_CHOICES, default="admin.dashboard")
    module = models.CharField(max_length=255, choices=ADMIN_MODULES_CHOICES, default="latest_users")
    status = models.BooleanField(default=True)
    order = models.IntegerField(default=0, null=False, blank=False, verbose_name=_("order"))
    created_at = models.DateTimeField(default=timezone.now, verbose_name=_("create at"))
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "page", "module")
        ordering = ('order',)

    def __str__(self):
        return f"{self.page} - {self.module}"

class TerminalDimensions(models.Model):
    module = models.ForeignKey(TerminalPageModule, on_delete=models.CASCADE, related_name='dimensions')
    breakpoint = models.CharField(
        max_length=255,
        choices=(('md', 'md'), ('sm', 'sm'), ('xs', 'xs'), ('lg', 'lg'))
    )
    w = models.IntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(12)])
    h = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    x = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(11)])
    y = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    moved = models.BooleanField(default=False)
    static = models.BooleanField(default=False)
    isResizable = models.BooleanField(default=False)

    class Meta:
        unique_together = ("module" ,"breakpoint", "w", "h", "x", "y", "moved", "static", "isResizable",)

class AdminDimensions(models.Model):
    module = models.ForeignKey(AdminPageModule, on_delete=models.CASCADE, related_name='dimensions')
    breakpoint = models.CharField(
        max_length=255,
        choices=(('md', 'md'), ('sm', 'sm'), ('xs', 'xs'), ('lg', 'lg'))
    )
    w = models.IntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(12)])
    h = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    x = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(11)])
    y = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    moved = models.BooleanField(default=False)
    static = models.BooleanField(default=False)
    isResizable = models.BooleanField(default=False)

    class Meta:
        unique_together = ("module" ,"breakpoint",)

class ThemeSettings(models.Model):
    MODE_CHOICES = (
        ('light', 'Light'),
        ('dark', 'Dark'),
    )

    DIRECTION_CHOICES = (
        ('rtl', 'Right to Left'),
        ('ltr', 'Left to Right'),
    )

    COLOR_CHOICES = (
        ('default', 'Default'),
        ('purple', 'Purple'),
        ('cyan', 'Cyan'),
        ('blue', 'Blue'),
        ('orange', 'Orange'),
        ('red', 'Red'),
    )

    LAYOUT_CHOICES = (
        ('horizontal', 'Horizontal'),
        ('vertical', 'Vertical'),
    )

    mode = models.CharField(max_length=5, choices=MODE_CHOICES, default='light')
    direction = models.CharField(max_length=3, choices=DIRECTION_CHOICES, default='ltr')
    color = models.CharField(max_length=7, choices=COLOR_CHOICES, default='default')
    stretch = models.BooleanField(default=False)
    layout = models.CharField(max_length=15, choices=LAYOUT_CHOICES, default='vertical')

    def __str__(self):
        return "Global Theme Settings"