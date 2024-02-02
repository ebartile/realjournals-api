from django.conf import settings
import ipaddress
import socket
from urllib.parse import urlparse

urls = {
    "admin": {
        "home": "/",
    },
    "terminal": {
        "home": "/",
        "pricing": "/pricing",
        "features": "/features",
        "about-us": "/about-us",
        "contact-us": "/contact-us",
        "faq": "/faq",
        "privacy-policy": "/privacy-policy",
        "terms-of-use": "/terms-of-use",

        "new-account": "/account/new",
        "new-account-import": "/account/new/import/{0}",
        "settings-mail-notifications": "/user-settings/mail-notifications",
        "account": "/account/{0}", # account.slug
        "team": "/account/{0}/team/", # account.slug
        "account-admin": "/login?next=/account/{0}/admin/account-profile/details", # account.slug


        "login": "/login",
        "register": "/register",
        "forgot-password": "/forgot-password",
        "change-password": "/change-password/{0}", # user.token
        "verify-email": "/verify-email/{0}", # user.email_token
        "change-email": "/change-email/{0}", # user.email_token
        "cancel-account": "/cancel-account/{0}", # auth.token.get_token_for_user(user)
        "invitation": "/invitation/{0}", # membership.token

        "user": "/profile/{0}", # user.username
    }
}

URL_TEMPLATE = "{scheme}://{domain}/{path}"

def build_url(path, scheme="http", domain="localhost"):
    return URL_TEMPLATE.format(scheme=scheme, domain=domain, path=path.lstrip("/"))

def is_absolute_url(path):
    """Test wether or not `path` is absolute url."""
    return path.startswith("http")

def get_absolute_url(path):
    """Return a path as an absolute url."""
    if is_absolute_url(path):
        return path
    return build_url(path, scheme="https", domain=settings.API_HOST)

class HostnameException(Exception):
    pass


class IpAddresValueError(ValueError):
    pass


def validate_private_url(url):
    host = urlparse(url).hostname
    port = urlparse(url).port

    try:
        socket_args, *others = socket.getaddrinfo(host, port)
    except Exception:
        raise HostnameException(_("Host access error"))

    destination_address = socket_args[4][0]
    try:
        ipa = ipaddress.ip_address(destination_address)
    except ValueError:
        raise IpAddresValueError(_("IP Address error"))
    if ipa.is_private:
        raise IpAddresValueError("Private IP Address not allowed")