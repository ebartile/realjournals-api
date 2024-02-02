from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Model
from django.test.utils import override_settings

from apps.accounts.models import Account
from .models import Timeline
from .service import _get_impl_key_from_model, _timeline_impl_map, extract_user_info

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

