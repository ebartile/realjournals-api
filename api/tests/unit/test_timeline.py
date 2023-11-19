# -*- coding: utf-8 -*-

from unittest.mock import patch, call

from django.contrib.auth import get_user_model

from apps.timeline import service
from apps.timeline.models import Timeline
from apps.accounts.models import Account

import pytest

pytestmark = pytest.mark.django_db(transaction=True)

def test_push_to_timeline_many_objects():
    with patch("apps.timeline.service._add_to_object_timeline") as mock:
        users = [get_user_model(), get_user_model(), get_user_model()]
        owner = get_user_model()
        account = Account()
        service._push_to_timeline(users, account, "test", account.created_date)
        assert mock.call_count == 3
        assert mock.mock_calls == [
            call(users[0], account, "test", account.created_date, "default", {}),
            call(users[1], account, "test", account.created_date, "default", {}),
            call(users[2], account, "test", account.created_date, "default", {}),
        ]
        with pytest.raises(Exception):
            service._push_to_timeline(None, account, "test")


def test_add_to_objects_timeline():
    with patch("apps.timeline.service._add_to_object_timeline") as mock:
        users = [get_user_model(), get_user_model(), get_user_model()]
        account = Account()
        service._add_to_objects_timeline(users, account, "test", account.created_date)
        assert mock.call_count == 3
        assert mock.mock_calls == [
            call(users[0], account, "test", account.created_date, "default", {}),
            call(users[1], account, "test", account.created_date, "default", {}),
            call(users[2], account, "test", account.created_date, "default", {}),
        ]
        with pytest.raises(Exception):
            service._push_to_timeline(None, account, "test")


def test_get_impl_key_from_model():
    assert service._get_impl_key_from_model(Timeline, "test") == "timeline.timeline.test"
    with pytest.raises(Exception):
        service._get_impl_key(None)


def test_get_impl_key_from_typename():
    assert service._get_impl_key_from_typename("timeline.timeline", "test") == "timeline.timeline.test"
    with pytest.raises(Exception):
        service._get_impl_key(None)


def test_register_timeline_implementation():
    test_func = lambda x: "test-func-result"
    service.register_timeline_implementation("timeline.timeline", "test", test_func)
    assert service._timeline_impl_map["timeline.timeline.test"](None) == "test-func-result"

    @service.register_timeline_implementation("timeline.timeline", "test-decorator")
    def decorated_test_function(x):
        return "test-decorated-func-result"

    assert service._timeline_impl_map["timeline.timeline.test-decorator"](None) == "test-decorated-func-result"