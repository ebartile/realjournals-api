from apps.utils.mails import mail_builder
from django.core.exceptions import ObjectDoesNotExist
from django.apps import apps
from django.conf import settings
from apps.utils.thumbnails import get_thumbnail_url
from .choices import ADMINS_PERMISSIONS, MEMBERS_PERMISSIONS, ANON_PERMISSIONS, BLOCKED_BY_DELETING
from django.db.models import Q
from . import models
from contextlib import suppress
from apps.utils.exceptions import BadRequest
from django.utils.translation import gettext_lazy as _
from realjournals.celery import app
from apps.accounts import tasks

def get_visible_account_ids(from_user, by_user):
    """Calculate the account_ids from one user visible by another"""
    required_permissions = ["view_account"]
    # Or condition for membership filtering, the basic one is the access to accounts
    # allowing public visualization
    member_perm_conditions = Q(account__public_permissions__contains=required_permissions)

    # Authenticated
    if by_user.is_authenticated:
        # Calculating the accounts wich from_user user is member
        by_user_account_ids = by_user.memberships.values_list("account__id", flat=True)
        # Adding to the condition two OR situations:
        # - The from user has a role that allows access to the account
        # - The to user is the owner
        member_perm_conditions |= \
            Q(account__id__in=by_user_account_ids, role__permissions__contains=required_permissions) |\
            Q(account__id__in=by_user_account_ids, is_admin=True)

    Membership = apps.get_model('accounts', 'Membership')
    # Calculating the user memberships adding the permission filter for the by user
    memberships_qs = Membership.objects.filter(member_perm_conditions, user=from_user)
    account_ids = memberships_qs.values_list("account__id", flat=True)
    return account_ids

def _get_object_account(obj):
    account = None
    Account = apps.get_model("accounts", "Account")
    if isinstance(obj, Account):
        account = obj
    elif obj and hasattr(obj, 'account'):
        account = obj.account
    return account

def _get_user_account_membership(user, account, cache="user"):
    """
    cache param determines how memberships are calculated trying to reuse the existing data
    in cache
    """
    if user.is_anonymous:
        return None

    if cache == "user":
        return user.cached_membership_for_account(account)

    return account.cached_memberships_for_user(user)


def calculate_permissions(is_authenticated=False, is_superuser=False, is_member=False,
                          is_admin=False, role_permissions=[], anon_permissions=[],
                          public_permissions=[]):
    if is_superuser:
        admins_permissions = list(map(lambda perm: perm[0], ADMINS_PERMISSIONS))
        members_permissions = list(map(lambda perm: perm[0], MEMBERS_PERMISSIONS))
        public_permissions = []
        anon_permissions = list(map(lambda perm: perm[0], ANON_PERMISSIONS))
    elif is_member:
        if is_admin:
            admins_permissions = list(map(lambda perm: perm[0], ADMINS_PERMISSIONS))
            members_permissions = list(map(lambda perm: perm[0], MEMBERS_PERMISSIONS))
        else:
            admins_permissions = []
            members_permissions = []
        members_permissions = members_permissions + role_permissions
        public_permissions = public_permissions if public_permissions is not None else []
        anon_permissions = anon_permissions if anon_permissions is not None else []
    elif is_authenticated:
        admins_permissions = []
        members_permissions = []
        public_permissions = public_permissions if public_permissions is not None else []
        anon_permissions = anon_permissions if anon_permissions is not None else []
    else:
        admins_permissions = []
        members_permissions = []
        public_permissions = []
        anon_permissions = anon_permissions if anon_permissions is not None else []

    return set(admins_permissions + members_permissions + public_permissions + anon_permissions)

def _get_membership_permissions(membership):
    if membership and membership.role and membership.role.permissions:
        return membership.role.permissions
    return []

def get_user_account_permissions(user, account, cache="user"):
    """
    cache param determines how memberships are calculated trying to reuse the existing data
    in cache
    """
    membership = _get_user_account_membership(user, account, cache=cache)
    is_member = membership is not None
    is_admin = is_member and membership.is_admin
    return calculate_permissions(
        is_authenticated = user.is_authenticated,
        is_superuser =  user.is_superuser,
        is_member = is_member,
        is_admin = is_admin,
        role_permissions = _get_membership_permissions(membership),
        anon_permissions = account.anon_permissions,
        public_permissions = account.public_permissions
    )

def user_has_perm(user, perm, obj=None, cache="user"):
    """
    cache param determines how memberships are calculated trying to reuse the existing data
    in cache
    """
    account = _get_object_account(obj)
    if not account:
        return False

    return perm in get_user_account_permissions(user, account, cache=cache)


def is_account_admin(user, obj):
    if user.is_superuser:
        return True

    account = _get_object_account(obj)
    if account is None:
        return False

    membership = _get_user_account_membership(user, account)
    if membership and membership.is_admin:
        return True

    return False

def account_has_valid_admins(account, exclude_user=None):
    """
    Checks if the account has any owner membership with a user different than the specified
    """
    admin_memberships = account.memberships.filter(is_admin=True, user__is_active=True)
    if exclude_user:
        admin_memberships = admin_memberships.exclude(user=exclude_user)

    return admin_memberships.count() > 0

def can_user_leave_account(user, account):
    membership = account.memberships.get(user=user)
    if not membership.is_admin:
        return True

    # The user can't leave if is the real owner of the account
    if account.owner == user:
        return False

    if not account_has_valid_admins(account, exclude_user=user):
        return False

    return True

def get_logo_small_thumbnail_url(account):
    if account.logo:
        return get_thumbnail_url(account.logo, settings.THN_LOGO_SMALL)
    return None


def get_logo_big_thumbnail_url(account):
    if account.logo:
        return get_thumbnail_url(account.logo, settings.THN_LOGO_BIG)
    return None

ERROR_MAX_PUBLIC_ACCOUNTS_MEMBERSHIPS = 'max_public_accounts_memberships'
ERROR_MAX_PRIVATE_ACCOUNTS_MEMBERSHIPS = 'max_private_accounts_memberships'
ERROR_MAX_PUBLIC_ACCOUNTS = 'max_public_accounts'
ERROR_MAX_PRIVATE_ACCOUNTS = 'max_private_accounts'
ERROR_ACCOUNT_WITHOUT_OWNER = 'account_without_owner'

def check_if_account_privacy_can_be_changed(
        account,
        current_memberships=None,
        current_private_accounts=None,
        current_public_accounts=None):
    """Return if the account privacy can be changed from private to public or viceversa.

    :param account: A account object.
    :param current_memberships: Account total memberships, If None it will be calculated.
    :param current_private_accounts: total private accounts owned by the account owner, If None it will be calculated.
    :param current_public_accounts: total public accounts owned by the account owner, If None it will be calculated.

    :return: A dict like this {'can_be_updated': bool, 'reason': error message}.
    """
    if account.owner is None:
        return {'can_be_updated': False, 'reason': ERROR_ACCOUNT_WITHOUT_OWNER}

    if current_memberships is None:
        current_memberships = account.memberships.count()

    if account.is_private:
        max_memberships = account.owner.max_memberships_public_accounts
        error_memberships_exceeded = ERROR_MAX_PUBLIC_ACCOUNTS_MEMBERSHIPS

        if current_public_accounts is None:
            current_accounts = account.owner.owned_accounts.filter(is_private=False).count()
        else:
            current_accounts = current_public_accounts

        max_accounts = account.owner.max_public_accounts
        error_account_exceeded = ERROR_MAX_PUBLIC_ACCOUNTS
    else:
        max_memberships = account.owner.max_memberships_private_accounts
        error_memberships_exceeded = ERROR_MAX_PRIVATE_ACCOUNTS_MEMBERSHIPS

        if current_private_accounts is None:
            current_accounts = account.owner.owned_accounts.filter(is_private=True).count()
        else:
            current_accounts = current_private_accounts

        max_accounts = account.owner.max_private_accounts
        error_account_exceeded = ERROR_MAX_PRIVATE_ACCOUNTS

    if max_memberships is not None and current_memberships > max_memberships:
        return {'can_be_updated': False, 'reason': error_memberships_exceeded}

    if max_accounts is not None and current_accounts >= max_accounts:
        return {'can_be_updated': False, 'reason': error_account_exceeded}

    return {'can_be_updated': True, 'reason': None}

def get_max_memberships_for_account(account):
    """Return tha maximun of membersh for a concrete account.

    :param account: A account object.

    :return: a number or null.
    """
    if account.owner is None:
        return None

    if account.is_private:
        return account.owner.max_memberships_private_accounts
    return account.owner.max_memberships_public_accounts


def check_if_account_is_out_of_owner_limits(
        account,
        current_memberships=None,
        current_private_accounts=None,
        current_public_accounts=None):

    """Return if the account fits on its owner limits.

    :param account: A account object.
    :param current_memberships: account total memberships, If None it will be calculated.
    :param current_private_accounts: total private accounts owned by the account owner, If None it will be calculated.
    :param current_public_accounts: total public accounts owned by the account owner, If None it will be calculated.

    :return: bool
    """
    if account.owner is None:
        return {'can_be_updated': False, 'reason': ERROR_ACCOUNT_WITHOUT_OWNER}

    if current_memberships is None:
        current_memberships = account.memberships.count()

    if account.is_private:
        max_memberships = account.owner.max_memberships_private_accounts

        if current_private_accounts is None:
            current_accounts = account.owner.owned_accounts.filter(is_private=True).count()
        else:
            current_accounts = current_private_accounts

        max_accounts = account.owner.max_private_accounts
    else:
        max_memberships = account.owner.max_memberships_public_accounts

        if current_public_accounts is None:
            current_accounts = account.owner.owned_accounts.filter(is_private=False).count()
        else:
            current_accounts = current_public_accounts

        max_accounts = account.owner.max_public_accounts

    if max_memberships is not None and current_memberships > max_memberships:
        return True

    if max_accounts is not None and current_accounts > max_accounts:
        return True

    return False

def is_account_owner(user, obj):
    account = _get_object_account(obj)
    if account is None:
        return False

    if user.id == account.owner_id:
        return True

    return False

def remove_user_from_account(user, account):
    if user == account.owner:
        raise BadRequest(_("You can't leave your own account."))
    models.Membership.objects.get(account=account, user=user).delete()

def update_accounts_order_in_bulk(bulk_data: list, field: str, user):
    """
    Update the order of user accounts in the user membership.
    `bulk_data` should be a list of dicts with the following format:

    [{'account_id': <value>, 'order': <value>}, ...]
    """
    memberships_orders = {m.id: getattr(m, field) for m in user.memberships.all()}
    new_memberships_orders = {}

    for membership_data in bulk_data:
        account_id = membership_data["account_id"]
        with suppress(ObjectDoesNotExist):
            membership = user.memberships.get(account_id=account_id)
            new_memberships_orders[membership.id] = membership_data["order"]

    apply_order_updates(memberships_orders, new_memberships_orders)

    from apps.utils import db
    db.update_attr_in_bulk_for_ids(memberships_orders, field, model=models.Membership)

def apply_order_updates(base_orders: dict, new_orders: dict, *, remove_equal_original=False):
    """
    `base_orders` must be a dict containing all the elements that can be affected by
    order modifications.
    `new_orders` must be a dict containing the basic order modifications to apply.

    The result will a base_orders with the specified order changes in new_orders
    and the extra calculated ones applied.
    Extra order updates can be needed when moving elements to intermediate positions.
    The elements where no order update is needed will be removed.
    """
    updated_order_ids = set()
    original_orders = {k: v for k, v in base_orders.items()}

    # Remove the elements from new_orders non existint in base_orders
    invalid_keys = new_orders.keys() - base_orders.keys()
    [new_orders.pop(id, None) for id in invalid_keys]

    # We will apply the multiple order changes by the new position order
    sorted_new_orders = [(k, v) for k, v in new_orders.items()]
    sorted_new_orders = sorted(sorted_new_orders, key=lambda e: e[1])

    for new_order in sorted_new_orders:
        old_order = base_orders[new_order[0]]
        new_order = new_order[1]
        for id, order in base_orders.items():
            # When moving forward only the elements contained in the range new_order - old_order
            # positions need to be updated
            moving_backward = new_order <= old_order and order >= new_order and order < old_order
            # When moving backward all the elements from the new_order position need to bee updated
            moving_forward = new_order >= old_order and order >= new_order
            if moving_backward or moving_forward:
                base_orders[id] += 1
                updated_order_ids.add(id)

    # Overwriting the orders specified
    for id, order in new_orders.items():
        if base_orders[id] != order:
            base_orders[id] = order
            updated_order_ids.add(id)

    # Remove not modified elements
    removing_keys = [id for id in base_orders if id not in updated_order_ids]
    [base_orders.pop(id, None) for id in removing_keys]

    # Remove the elements that remains the same
    if remove_equal_original:
        common_keys = base_orders.keys() & original_orders.keys()
        [base_orders.pop(id, None) for id in common_keys if original_orders[id] == base_orders[id]]

def orphan_account(account):
    account.memberships.filter(user=account.owner).delete()
    account.owner = None
    account.blocked_code = BLOCKED_BY_DELETING
    account.save()


@app.task
def delete_account(account_id):
    account = apps.get_model("accounts", "Account")
    try:
        account = models.Account.objects.get(id=account_id)
    except models.Account.DoesNotExist:
        return

    account.delete_related_content()
    account.delete()


@app.task
def delete_accounts(accounts):
    for account in accounts:
        delete_account(account.id)

def check_if_account_can_have_more_memberships(account, total_new_memberships):
    """Return if a account can have more n new memberships.

    :param account: A account object.
    :param total_new_memberships: the total of new memberships to add (int).

    :return: {bool, error_mesage} return a tuple (can add new members?, error message).
    """
    if account.owner is None:
        return False, _("Account without owner")

    if account.is_private:
        total_memberships = account.memberships.count() + total_new_memberships
        max_memberships = account.owner.max_memberships_private_accounts
        error_members_exceeded = _("You have reached your current limit of memberships for private accounts")
    else:
        total_memberships = account.memberships.count() + total_new_memberships
        max_memberships = account.owner.max_memberships_public_accounts
        error_members_exceeded = _("You have reached your current limit of memberships for public accounts")

    if max_memberships is not None and total_memberships > max_memberships:
        return False, error_members_exceeded

    if account.memberships.filter(user=None).count() + total_new_memberships > settings.MAX_PENDING_MEMBERSHIPS:
        error_pending_memberships_exceeded = _("You have reached the current limit of pending memberships")
        return False, error_pending_memberships_exceeded

    return True, None

def send_invitation(invitation):
    """Send an invitation email"""
    if invitation.user:
        template = mail_builder.membership_notification
        email = template(invitation.user, {"membership": invitation})
    else:
        template = mail_builder.membership_invitation
        email = template(invitation.email, {"membership": invitation})

    email.send()

def find_invited_user(email, default=None):
    """Check if the invited user is already a registered.

    :param invitation: Invitation object.
    :param default: Default object to return if user is not found.

    TODO: only used by importer/exporter and should be moved here

    :return: The user if it's found, othwerwise return `default`.
    """

    User = apps.get_model(settings.AUTH_USER_MODEL)

    try:
        return User.objects.get(email=email)
    except User.DoesNotExist:
        return default
