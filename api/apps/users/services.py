from django.conf import settings
from easy_thumbnails.files import get_thumbnailer
from easy_thumbnails.exceptions import InvalidImageFormatError
from apps.utils.urls import get_absolute_url
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from apps.utils.exceptions import WrongArguments
from django.db.models import Q

def get_user_by_email(email):
    user_model = get_user_model()
    qs = user_model.objects.filter(Q(email__iexact=email))

    if len(qs) > 1:
        qs = qs.filter(Q(email=email))

    if len(qs) == 0:
        raise WrongArguments(_("Email or password does not match user."))

    user = qs[0]
    return user

def get_photo_url(photo):
    """Get a photo absolute url and the photo automatically cropped."""
    if not photo:
        return None
    try:
        url = get_thumbnailer(photo)[settings.THN_AVATAR_SMALL].url
        return get_absolute_url(url)
    except InvalidImageFormatError as e:
        return None

def get_big_photo_url(photo):
    """Get a big photo absolute url and the photo automatically cropped."""
    if not photo:
        return None
    try:
        url = get_thumbnailer(photo)[settings.THN_AVATAR_BIG].url
        return get_absolute_url(url)
    except InvalidImageFormatError as e:
        return None

def get_user_big_photo_url(user):
    """Get the user's big photo url."""
    if not user:
        return None
    return get_big_photo_url(user.photo)


def get_user_photo_url(user):
    """Get the user's photo url."""
    if not user:
        return None
    return get_photo_url(user.photo)

def has_available_slot_for_new_account(owner, is_private, total_memberships):
    if is_private:
        current_account = owner.owned_accounts.filter(is_private=True).count()
        max_accounts = owner.max_private_accounts
        error_account_exceeded =  _("You can't have more private accounts")

        max_memberships = owner.max_memberships_private_accounts
        error_memberships_exceeded = _("This account reaches your current limit of memberships for private accounts")
    else:
        current_accounts = owner.owned_accounts.filter(is_private=False).count()
        max_accounts = owner.max_public_accounts
        error_account_exceeded = _("You can't have more public accounts")

        max_memberships = owner.max_memberships_public_accounts
        error_memberships_exceeded = _("This account reaches your current limit of memberships for public accounts")

    if max_accounts is not None and current_accounts >= max_accounts:
        return (False, error_account_exceeded)

    if max_memberships is not None and total_memberships > max_memberships:
        return (False, error_memberships_exceeded)

    return (True, None)
