from collections import OrderedDict

from .generics import GenericSitemap

from .accounts import AccountsSitemap

from .users import UsersSitemap

sitemaps = OrderedDict([
    ("generics", GenericSitemap),

    ("accounts", AccountsSitemap),

    ("users", UsersSitemap)
])
