from collections import OrderedDict

from .generics import GenericSitemap

from .accounts import AccountsSitemap

from .journals import JournalsSitemap

from .users import UsersSitemap

sitemaps = OrderedDict([
    ("generics", GenericSitemap),

    ("accounts", AccountsSitemap),

    ("issues", IssuesSitemap),

    ("users", UsersSitemap)
])
