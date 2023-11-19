from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Model
from django.test.utils import override_settings

from apps.accounts.models import Account
from apps.history.models import HistoryEntry
from .models import Timeline
from .service import _get_impl_key_from_model, _timeline_impl_map, extract_user_info
from .signals import on_new_history_entry, _push_to_timelines

from unittest.mock import patch

import gc


class BulkCreator(object):
    def __init__(self):
        self.timeline_objects = []
        self.created = None

    def create_element(self, element):
        self.timeline_objects.append(element)
        if len(self.timeline_objects) > 999:
            self.flush()

    def flush(self):
        Timeline.objects.bulk_create(self.timeline_objects, batch_size=1000)
        del self.timeline_objects
        self.timeline_objects = []
        gc.collect()

bulk_creator = BulkCreator()


def custom_add_to_object_timeline(obj:object, instance:object, event_type:str, created_datetime:object,
                                  namespace:str="default", extra_data:dict={}):
    assert isinstance(obj, Model), "obj must be a instance of Model"
    assert isinstance(instance, Model), "instance must be a instance of Model"
    event_type_key = _get_impl_key_from_model(instance.__class__, event_type)
    impl = _timeline_impl_map.get(event_type_key, None)

    bulk_creator.create_element(Timeline(
        content_object=obj,
        namespace=namespace,
        event_type=event_type_key,
        account=instance.account,
        data=impl(instance, extra_data=extra_data),
        data_content_type=ContentType.objects.get_for_model(instance.__class__),
        created=created_datetime,
    ))


@override_settings(CELERY_ENABLED=False)
def rebuild_timeline(initial_date, final_date, account_id):
    if initial_date or final_date or account_id:
        timelines = Timeline.objects.all()
        if initial_date:
            timelines = timelines.filter(created__gte=initial_date)
        if final_date:
            timelines = timelines.filter(created__lt=final_date)
        if account_id:
            timelines = timelines.filter(account__id=account_id)

        timelines.delete()

    with patch('apps.timeline.service._add_to_object_timeline', new=custom_add_to_object_timeline):
        # accounts api wasn't a HistoryResourceMixin so we can't interate on the HistoryEntries in this case
        accounts = Account.objects.order_by("created_date")
        history_entries = HistoryEntry.objects.order_by("created_at")

        if initial_date:
            accounts = accounts.filter(created_date__gte=initial_date)
            history_entries = history_entries.filter(created_at__gte=initial_date)

        if final_date:
            accounts = accounts.filter(created_date__lt=final_date)
            history_entries = history_entries.filter(created_at__lt=final_date)

        if account_id:
            account = Account.objects.get(id=account_id)
            journal_keys = ['journals.journal:%s'%(id) for id in account.journals.values_list("id", flat=True)]
            keys = journal_keys

            accounts = accounts.filter(id=account_id)
            history_entries = history_entries.filter(key__in=keys)

            #Memberships
            for membership in account.memberships.exclude(user=None).exclude(user=account.owner):
                _push_to_timelines(account, membership.user, membership, "create", membership.created_at)

        for account in accounts.iterator():
            print("Account:", account)
            extra_data = {
                "values_diff": {},
                "user": extract_user_info(account.owner),
            }
            _push_to_timelines(account, account.owner, account, 'create',
                               account.created_date, extra_data=extra_data)
            del extra_data

        for historyEntry in history_entries.iterator():
            print("History entry:", historyEntry.created_at)
            try:
                on_new_history_entry(None, historyEntry, None)
            except ObjectDoesNotExist as e:
                print("Ignoring")

    bulk_creator.flush()
