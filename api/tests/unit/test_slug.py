# -*- coding: utf-8 -*-
import pytest

from django.contrib.auth import get_user_model

from apps.accounts.models import Account
from apps.utils.slug import slugify

from tests.utils import disconnect_signals, reconnect_signals


def setup_module():
    disconnect_signals()


def teardown_module():
    reconnect_signals()


def test_slugify_1():
    assert slugify("漢字") == "han-zi"


def test_slugify_2():
    assert slugify("TestExamplePage") == "testexamplepage"


def test_slugify_3():
    assert slugify(None) == ""


@pytest.mark.django_db
def test_account_slug_with_special_chars():
    user = get_user_model().objects.create(username="test")
    account = Account.objects.create(name="漢字", description="漢字", owner=user)
    account.save()

    assert account.slug == "test-han-zi"


@pytest.mark.django_db
def test_account_with_existing_name_slug_with_special_chars():
    user = get_user_model().objects.create(username="test")
    Account.objects.create(name="漢字", description="漢字", owner=user)
    account = Account.objects.create(name="漢字", description="漢字", owner=user)

    assert account.slug == "test-han-zi-1"