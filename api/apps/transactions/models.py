from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.conf import settings

class Transaction(models.Model):
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    owner = models.ForeignKey(
            settings.AUTH_USER_MODEL,
            null=True,
            blank=True,
            default=None,
            related_name="owned_transactions",
            verbose_name=_("owner"),
            on_delete=models.SET_NULL,
        )
    account = models.ForeignKey(
        "accounts.Account",
        null=False,
        blank=False,
        related_name="transactions",
        verbose_name=_("account"),
        on_delete=models.CASCADE,
    )
