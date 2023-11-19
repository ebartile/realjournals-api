import uuid

from django.utils import timezone
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.functional import cached_property

from apps.utils.mdrender.service import get_diff_of_htmls

from .choices import HistoryType
from .choices import HISTORY_TYPE_CHOICES

from apps.utils.diff import make_diff as make_diff_from_dicts
from apps.journals.models import CHECKBOX_TYPE, NUMBER_TYPE, TEXT_TYPE

# This keys has been removed from freeze_impl so we can have objects where the
# previous diff has value for the attribute and we want to prevent their propagation
IGNORE_DIFF_FIELDS = ["watchers", "description_diff", "content_diff", "blocked_note_diff"]


def _generate_uuid():
    return str(uuid.uuid1())


class HistoryEntry(models.Model):
    """
    Domain model that represents a history
    entry storage table.

    It is used for store object changes and
    comments.
    """
    id = models.CharField(primary_key=True, max_length=255, unique=True,
                          editable=False, default=_generate_uuid)
    account = models.ForeignKey("accounts.Account", on_delete=models.CASCADE)
    user = models.JSONField(null=True, blank=True, default=None)
    created_at = models.DateTimeField(default=timezone.now)
    type = models.SmallIntegerField(choices=HISTORY_TYPE_CHOICES)
    key = models.CharField(max_length=255, null=True, default=None, blank=True, db_index=True)

    # Stores the last diff
    diff = models.JSONField(null=True, blank=True, default=None)

    # Stores the values_diff cache
    values_diff_cache = models.JSONField(null=True, blank=True, default=None)

    # Stores the last complete frozen object snapshot
    snapshot = models.JSONField(null=True, blank=True, default=None)

    # Stores a values of all identifiers used in
    values = models.JSONField(null=True, blank=True, default=None)

    # Stores a comment
    comment = models.TextField(blank=True)
    comment_html = models.TextField(blank=True)

    delete_comment_date = models.DateTimeField(null=True, blank=True, default=None)
    delete_comment_user = models.JSONField(null=True, blank=True, default=None)

    # Historic version of comments
    comment_versions = models.JSONField(null=True, blank=True, default=None)
    edit_comment_date = models.DateTimeField(null=True, blank=True, default=None)

    # Flag for mark some history entries as
    # hidden. Hidden history entries are important
    # for save but not important to preview.
    # Order fields are the good example of this fields.
    is_hidden = models.BooleanField(default=False)

    # Flag for mark some history entries as complete
    # snapshot. The rest are partial snapshot.
    is_snapshot = models.BooleanField(default=False)

    _owner = None
    _prefetched_owner = False

    @cached_property
    def is_change(self):
        return self.type == HistoryType.change

    @cached_property
    def is_create(self):
        return self.type == HistoryType.create

    @cached_property
    def is_delete(self):
        return self.type == HistoryType.delete

    @property
    def owner(self):
        if not self._prefetched_owner:
            pk = self.user["pk"]
            model = get_user_model()
            try:
                owner = model.objects.get(pk=pk)
            except model.DoesNotExist:
                owner = None

            self.prefetch_owner(owner)

        return self._owner

    def prefetch_owner(self, owner):
        self._owner = owner
        self._prefetched_owner = True

    def attach_user_info_to_comment_versions(self):
        if not self.comment_versions:
            return

        from apps.users.serializers import UserSerializer

        user_ids = [v["user"]["id"] for v in self.comment_versions if "user" in v and "id" in v["user"]]
        users_by_id = {u.id: u for u in get_user_model().objects.filter(id__in=user_ids)}

        for version in self.comment_versions:
            user = users_by_id.get(version["user"]["id"], None)
            if user:
                version["user"] = UserSerializer(user).data

    @property
    def values_diff(self):
        if self.values_diff_cache is not None:
            return self.values_diff_cache

        result = {}
        users_keys = ["assigned_to", "owner"]

        def resolve_diff_value(key):
            value = None
            diff = get_diff_of_htmls(
                self.diff[key][0] or "",
                self.diff[key][1] or ""
            )

            if diff:
                key = "{}_diff".format(key)
                value = (None, diff)

            return (key, value)

        def resolve_value(field, key):
            data = self.values[field]
            key = str(key)

            if key not in data:
                return None
            return data[key]

        for key in self.diff:
            value = None
            if key in IGNORE_DIFF_FIELDS:
                continue
            elif key in["description", "content", "blocked_note"]:
                (key, value) = resolve_diff_value(key)
            elif key in users_keys:
                value = [resolve_value("users", x) for x in self.diff[key]]
            elif key == "assigned_users":
                diff_in, diff_out = self.diff[key]
                value_in = None
                value_out = None

                if diff_in:
                    users_list = [resolve_value("users", x) for x in diff_in if x]
                    value_in = ", ".join(filter(None, users_list))
                if diff_out:
                    users_list = [resolve_value("users", x) for x in diff_out if x]
                    value_out = ", ".join(filter(None, users_list))
                value = [value_in, value_out]

            elif key == "attachments":
                attachments = {
                    "new": [],
                    "changed": [],
                    "deleted": [],
                }

                oldattachs = {x["id"]: x for x in self.diff["attachments"][0]}
                newattachs = {x["id"]: x for x in self.diff["attachments"][1]}

                for aid in set(tuple(oldattachs.keys()) + tuple(newattachs.keys())):
                    if aid in oldattachs and aid in newattachs:
                        changes = make_diff_from_dicts(oldattachs[aid], newattachs[aid],
                                                       excluded_keys=("filename", "url", "thumb_url"))

                        if changes:
                            change = {
                                "filename": newattachs.get(aid, {}).get("filename", ""),
                                "url": newattachs.get(aid, {}).get("url", ""),
                                "thumb_url": newattachs.get(aid, {}).get("thumb_url", ""),
                                "changes": changes
                            }
                            attachments["changed"].append(change)
                    elif aid in oldattachs and aid not in newattachs:
                        attachments["deleted"].append(oldattachs[aid])
                    elif aid not in oldattachs and aid in newattachs:
                        attachments["new"].append(newattachs[aid])

                if attachments["new"] or attachments["changed"] or attachments["deleted"]:
                    value = attachments

            elif key == "custom_attributes":
                custom_attributes = {
                    "new": [],
                    "changed": [],
                    "deleted": [],
                }

                oldcustattrs = {x["id"]: x for x in self.diff["custom_attributes"][0] or []}
                newcustattrs = {x["id"]: x for x in self.diff["custom_attributes"][1] or []}

                for aid in set(tuple(oldcustattrs.keys()) + tuple(newcustattrs.keys())):
                    if aid in oldcustattrs and aid in newcustattrs:
                        changes = make_diff_from_dicts(oldcustattrs[aid], newcustattrs[aid],
                                                       excluded_keys=("name", "type"))
                        newcustattr = newcustattrs.get(aid, {})
                        if changes:
                            change_type = newcustattr.get("type", TEXT_TYPE)

                            if change_type in [NUMBER_TYPE, CHECKBOX_TYPE]:
                                old_value = oldcustattrs[aid].get("value")
                                new_value = newcustattrs[aid].get("value")
                                value_diff = [old_value, new_value]
                            else:
                                old_value = oldcustattrs[aid].get("value", "")
                                new_value = newcustattrs[aid].get("value", "")
                                value_diff = get_diff_of_htmls(old_value,
                                                               new_value)
                            change = {
                                "name": newcustattr.get("name", ""),
                                "changes": changes,
                                "type": change_type,
                                "value_diff": value_diff
                            }
                            custom_attributes["changed"].append(change)
                    elif aid in oldcustattrs and aid not in newcustattrs:
                        custom_attributes["deleted"].append(oldcustattrs[aid])
                    elif aid not in oldcustattrs and aid in newcustattrs:
                        newcustattr = newcustattrs.get(aid, {})
                        change_type = newcustattr.get("type", TEXT_TYPE)
                        if change_type in [NUMBER_TYPE, CHECKBOX_TYPE]:
                            old_value = None
                            new_value = newcustattrs[aid].get("value")
                            value_diff = [old_value, new_value]
                        else:
                            new_value = newcustattrs[aid].get("value", "")
                            value_diff = get_diff_of_htmls("", new_value)
                        newcustattrs[aid]["value_diff"] = value_diff
                        custom_attributes["new"].append(newcustattrs[aid])

                if custom_attributes["new"] or custom_attributes["changed"] or custom_attributes["deleted"]:
                    value = custom_attributes

            elif key in self.values:
                value = [resolve_value(key, x) for x in self.diff[key]]
            else:
                value = self.diff[key]

            if not value:
                continue

            result[key] = value

        self.values_diff_cache = result
        # Update values_diff_cache without dispatching signals
        HistoryEntry.objects.filter(pk=self.pk).update(values_diff_cache=self.values_diff_cache)
        return self.values_diff_cache

    class Meta:
        ordering = ["created_at"]
