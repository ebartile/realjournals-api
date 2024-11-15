from django.conf import settings

import hashlib
import functools
import bleach

# BEGIN PATCH
import html5lib
from html5lib.serializer import HTMLSerializer


def _serialize(domtree):
    walker = html5lib.treewalkers.getTreeWalker('etree')
    stream = walker(domtree)
    serializer = HTMLSerializer(quote_attr_values=True,
                                omit_optional_tags=False,
                                alphabetical_attributes=True)

    return serializer.render(stream)

bleach._serialize = _serialize
# END PATCH

from django.core.cache import cache
from django.utils.encoding import force_bytes

from markdown import Markdown

from .extensions.autolink import AutolinkExtension
from .extensions.automail import AutomailExtension
from .extensions.semi_sane_lists import SemiSaneListExtension
from .extensions.strikethrough import StrikethroughExtension
from .extensions.emojify import EmojifyExtension
from .extensions.mentions import MentionsExtension
from .extensions.references import RealJournalsReferencesExtension
from .extensions.target_link import TargetBlankLinkExtension
from .extensions.refresh_attachment import RefreshAttachmentExtension

# Bleach configuration
bleach.ALLOWED_TAGS += ["p", "table", "thead", "tbody", "th", "tr", "td", "h1",
                        "h2", "h3", "h4", "h5", "h6", "div", "pre", "span",
                        "hr", "dl", "dt", "dd", "sup", "img", "del", "br",
                        "ins"]

bleach.ALLOWED_STYLES.append("background")

bleach.ALLOWED_ATTRIBUTES["a"] = ["href", "title", "alt", "target"]
bleach.ALLOWED_ATTRIBUTES["img"] = ["alt", "src"]
bleach.ALLOWED_ATTRIBUTES["*"] = ["class", "style", "id"]


def _make_extensions_list(account=None):
    return [AutolinkExtension(),
            AutomailExtension(),
            SemiSaneListExtension(),
            StrikethroughExtension(),
            EmojifyExtension(),
            MentionsExtension(account=account),
            RealJournalsReferencesExtension(account),
            TargetBlankLinkExtension(),
            RefreshAttachmentExtension(account=account),
            "markdown.extensions.extra",
            "markdown.extensions.codehilite",
            "markdown.extensions.sane_lists",
            "markdown.extensions.toc",
            "markdown.extensions.nl2br"]


import diff_match_patch


def cache_by_sha(func):
    @functools.wraps(func)
    def _decorator(account, text):
        if not settings.MDRENDER_CACHE_ENABLE:
            return func(account, text)

        # Avoid cache of too short texts
        if len(text) <= settings.MDRENDER_CACHE_MIN_SIZE:
            return func(account, text)

        sha1_hash = hashlib.sha1(force_bytes(text)).hexdigest()
        key = "mdrender/{}-{}".format(sha1_hash, account.id)

        # Try to get it from the cache
        cached = cache.get(key)
        if cached is not None:
            return cached

        returned_value = func(account, text)
        cache.set(key, returned_value, timeout=settings.MDRENDER_CACHE_TIMEOUT)
        return returned_value

    return _decorator


def _get_markdown(account):
    extensions = _make_extensions_list(account=account)
    md = Markdown(extensions=extensions)
    md.extracted_data = {"mentions": [], "references": []}
    return md


@cache_by_sha
def render(account, text):
    md = _get_markdown(account)
    return bleach.clean(md.convert(text))


def render_and_extract(account, text):
    md = _get_markdown(account)
    result = bleach.clean(md.convert(text))
    return (result, md.extracted_data)


class DiffMatchPatch(diff_match_patch.diff_match_patch):
    def diff_pretty_html(self, diffs):
        def _sanitize_text(text):
            return (text.replace("&", "&amp;").replace("<", "&lt;")
                        .replace(">", "&gt;").replace("\n", "<br />"))

        def _split_long_text(text, idx, size):
            splited_text = text.split()

            if len(splited_text) > 25:
                if idx == 0:
                    # The first is (...)text
                    first = ""
                else:
                    first = " ".join(splited_text[:10])

                if idx != 0 and idx == size - 1:
                    # The last is text(...)
                    last = ""
                else:
                    last = " ".join(splited_text[-10:])

                return "{}(...){}".format(first, last)
            return text

        size = len(diffs)
        html = []
        for idx, (op, data) in enumerate(diffs):
            if op == self.DIFF_INSERT:
                text = _sanitize_text(data)
                html.append("<ins style=\"background:#e6ffe6;\">{}</ins>".format(text))
            elif op == self.DIFF_DELETE:
                text = _sanitize_text(data)
                html.append("<del style=\"background:#ffe6e6;\">{}</del>".format(text))
            elif op == self.DIFF_EQUAL:
                text = _split_long_text(_sanitize_text(data), idx, size)
                html.append("<span>{}</span>".format(text))

        return "".join(html)


def get_diff_of_htmls(html1, html2):
    diffutil = DiffMatchPatch()
    diffs = diffutil.diff_main(html1 or "", html2 or "")
    diffutil.diff_cleanupSemantic(diffs)
    return diffutil.diff_pretty_html(diffs)


__all__ = ["render", "get_diff_of_htmls", "render_and_extract"]
