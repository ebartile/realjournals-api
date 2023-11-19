import markdown

STRIKE_RE = r'(~{2})(.+?)(~{2})'  # ~~strike~~


class StrikethroughExtension(markdown.Extension):
    """An extension that supports PHP-Markdown style strikethrough.

    For example: ``~~strike~~``.
    """

    def extendMarkdown(self, md):
        pattern = markdown.inlinepatterns.SimpleTagPattern(STRIKE_RE, 'del')
        md.inlinePatterns.add('gfm-strikethrough', pattern, '_end')
