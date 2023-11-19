from django.apps import AppConfig
from django.db.models import signals
from django.apps import apps

## Account Signals

def connect_accounts_signals():
    from . import signals as handlers
    # On account object is created apply template.
    signals.post_save.connect(handlers.account_post_save,
                              sender=apps.get_model("accounts", "Account"),
                              dispatch_uid='account_post_save')


def disconnect_accounts_signals():
    signals.post_save.disconnect(sender=apps.get_model("accounts", "Account"),
                                 dispatch_uid='account_post_save')

## Memberships Signals

def connect_memberships_signals():
    from . import signals as handlers
    # On membership object is created, reorder and create notify policies
    signals.post_save.connect(handlers.membership_post_save,
                              sender=apps.get_model("accounts", "Membership"),
                              dispatch_uid='membership_post_save')


def disconnect_memberships_signals():
    signals.post_save.disconnect(sender=apps.get_model("accounts", "Membership"),
                                 dispatch_uid='membership_post_save')

class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.accounts'

    def ready(self):
        connect_accounts_signals()
        connect_memberships_signals()
