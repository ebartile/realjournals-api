import markdown
from markdown.treeprocessors import Treeprocessor

from apps.attachments.services import (
    extract_refresh_id, get_attachment_by_id, generate_refresh_fragment, url_is_an_attachment
)

class RefreshAttachmentExtension(markdown.Extension):
    """An extension that refresh attachment URL."""
    def __init__(self, *args, **kwargs):
        self.account = kwargs.pop("account", None)
        super().__init__(*args, **kwargs)

    def extendMarkdown(self, md):
        md.treeprocessors.add("refresh_attachment",
                              RefreshAttachmentTreeprocessor(md, account=self.account),
                              "<prettify")


class RefreshAttachmentTreeprocessor(Treeprocessor):
    def __init__(self, *args, **kwargs):
        self.account = kwargs.pop("account", None)
        super().__init__(*args, **kwargs)

    def run(self, root):
        # Bypass if not account
        if not self.account:
            return

        for tag, attr in [("img", "src"), ("a", "href")]:
            for el in root.iter(tag):
                url = url_is_an_attachment(el.get(attr, ""))
                if not url:
                    # It's not an attachment
                    break

                type_, attachment_id = extract_refresh_id(url)
                if not attachment_id:
                    # There is no refresh parameter
                    break

                attachment = get_attachment_by_id(self.account.id, attachment_id)
                if not attachment:
                    # Attachment not found or not permissions
                    break

                # Substitute url
                frag = generate_refresh_fragment(attachment, type_)
                new_url = "{}#{}".format(attachment.attached_file.url, frag)
                el.set(attr, new_url)
