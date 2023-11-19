
import re
import markdown

from markdown.treeprocessors import Treeprocessor

from apps.users.templatetags.functions import resolve_landing


class TargetBlankLinkExtension(markdown.Extension):
    """An extension that add target="_blank" to all external links."""
    def extendMarkdown(self, md):
        md.treeprocessors.add("target_blank_links",
                              TargetBlankLinksTreeprocessor(md),
                              "<prettify")


class TargetBlankLinksTreeprocessor(Treeprocessor):
    def run(self, root):
        home_url = resolve_landing("home")
        links = root.iter("a")
        for a in links:
            href = a.get("href", "")
            url = a.get("href", "")
            if url.endswith("/"):
                url = url[:-1]

            if not url.startswith(home_url):
                a.set("target", "_blank")
