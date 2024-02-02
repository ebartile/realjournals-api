from markdown.extensions import Extension
from markdown.inlinepatterns import Pattern
from markdown.util import etree

from apps.references.services import get_instance_by_ref
from apps.users.templatetags.functions import resolve_terminal


class RealJournalsReferencesExtension(Extension):
    def __init__(self, account, *args, **kwargs):
        self.account = account
        return super().__init__(*args, **kwargs)

    def extendMarkdown(self, md):
        REALJOURNALS_REFERENCE_RE = r'(?<=^|(?<=[^a-zA-Z0-9-\[]))#(\d+)'
        referencesPattern = RealJournalsReferencesPattern(REALJOURNALS_REFERENCE_RE, self.account)
        referencesPattern.md = md
        md.inlinePatterns.add('realjournals-references', referencesPattern, '_begin')


class RealJournalsReferencesPattern(Pattern):
    def __init__(self, pattern, account):
        self.account = account
        super().__init__(pattern)

    def handleMatch(self, m):
        obj_ref = m.group(2)

        instance = get_instance_by_ref(self.account.id, obj_ref)
        if instance is None or instance.content_object is None:
            return "#{}".format(obj_ref)

        subject = instance.content_object.subject

        if instance.content_type.model == "account":
            html_classes = "reference account"
        else:
            return "#{}".format(obj_ref)

        url = resolve_terminal(instance.content_type.model, self.account.slug, obj_ref)

        link_text = "&num;{}".format(obj_ref)

        a = etree.Element('a')
        a.text = link_text
        a.set('href', url)
        a.set('title', "#{} {}".format(obj_ref, subject))
        a.set('class', html_classes)

        self.md.extracted_data['references'].append(instance.content_object)

        return a
