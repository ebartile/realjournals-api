from django.contrib.auth import get_user_model

from markdown.extensions import Extension
from markdown.inlinepatterns import Pattern
from markdown.util import etree, AtomicString


class MentionsExtension(Extension):
    account = None

    def __init__(self, *args, **kwargs):
        self.account = kwargs.pop("account", None)
        super().__init__(*args, **kwargs)

    def extendMarkdown(self, md):
        MENTION_RE = r"(@)([\w.-]+)"
        mentionsPattern = MentionsPattern(MENTION_RE, account=self.account)
        mentionsPattern.md = md
        md.inlinePatterns.add("mentions", mentionsPattern, "_end")


class MentionsPattern(Pattern):
    account = None

    def __init__(self, pattern, md=None, account=None):
        self.account = account
        super().__init__(pattern, md)

    def handleMatch(self, m):
        username = m.group(3)
        kwargs = {"username": username}
        if self.account is not None:
            kwargs["memberships__account_id"]=self.account.id
        try:
            user = get_user_model().objects.get(**kwargs)
        except get_user_model().DoesNotExist:
            return "@{}".format(username)

        url = "/profile/{}".format(username)

        link_text = "@{}".format(username)

        a = etree.Element('a')
        a.text = AtomicString(link_text)

        a.set('href', url)
        a.set('title', user.get_full_name())
        a.set('class', "mention")

        self.md.extracted_data['mentions'].append(user)

        return a
