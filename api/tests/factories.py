# -*- coding: utf-8 -*-
import uuid
import threading
from datetime import date, timedelta

from django.conf import settings

from .utils import DUMMY_BMP_DATA

import factory

from apps.accounts.choices import MEMBERS_PERMISSIONS



class Factory(factory.django.DjangoModelFactory):
    class Meta:
        strategy = factory.CREATE_STRATEGY
        model = None
        abstract = True

    _SEQUENCE = 1
    _SEQUENCE_LOCK = threading.Lock()

    @classmethod
    def _setup_next_sequence(cls):
        with cls._SEQUENCE_LOCK:
            cls._SEQUENCE += 1
        return cls._SEQUENCE


class AccountFactory(Factory):
    class Meta:
        model = "accounts.Account"
        strategy = factory.CREATE_STRATEGY

    name = factory.Sequence(lambda n: "Account {}".format(n))
    slug = factory.Sequence(lambda n: "account-{}-slug".format(n))
    logo = factory.django.FileField(data=DUMMY_BMP_DATA)

    description = "Account description"
    owner = factory.SubFactory("tests.factories.UserFactory")


class RoleFactory(Factory):
    class Meta:
        model = "users.Role"
        strategy = factory.CREATE_STRATEGY

    name = factory.Sequence(lambda n: "Role {}".format(n))
    slug = factory.Sequence(lambda n: "test-role-{}".format(n))
    account = factory.SubFactory("tests.factories.AccountFactory")


class UserFactory(Factory):
    class Meta:
        model = settings.AUTH_USER_MODEL
        strategy = factory.CREATE_STRATEGY

    username = factory.Sequence(lambda n: "user{}".format(n))
    email = factory.LazyAttribute(lambda obj: '%s@email.com' % obj.username)
    password = factory.PostGeneration(lambda obj, *args, **kwargs: obj.set_password(obj.username))
    accepted_terms = True
    read_new_terms = True


class MembershipFactory(Factory):
    class Meta:
        model = "accounts.Membership"
        strategy = factory.CREATE_STRATEGY

    token = factory.LazyAttribute(lambda obj: str(uuid.uuid1()))
    account = factory.SubFactory("tests.factories.AccountFactory")
    role = factory.SubFactory("tests.factories.RoleFactory")
    user = factory.SubFactory("tests.factories.UserFactory")


class InvitationFactory(Factory):
    class Meta:
        model = "accounts.Membership"
        strategy = factory.CREATE_STRATEGY

    token = factory.LazyAttribute(lambda obj: str(uuid.uuid1()))
    account = factory.SubFactory("tests.factories.AccountFactory")
    role = factory.SubFactory("tests.factories.RoleFactory")
    email = factory.Sequence(lambda n: "user{}@email.com".format(n))


class StorageEntryFactory(Factory):
    class Meta:
        model = "userstorage.StorageEntry"
        strategy = factory.CREATE_STRATEGY

    owner = factory.SubFactory("tests.factories.UserFactory")
    key = factory.Sequence(lambda n: "key-{}".format(n))
    value = factory.Sequence(lambda n: {"value": "value-{}".format(n)})



class LikeFactory(Factory):
    class Meta:
        model = "likes.Like"
        strategy = factory.CREATE_STRATEGY

    content_type = factory.SubFactory("tests.factories.ContentTypeFactory")
    object_id = factory.Sequence(lambda n: n)
    user = factory.SubFactory("tests.factories.UserFactory")


class WatchedFactory(Factory):
    class Meta:
        model = "notifications.Watched"
        strategy = factory.CREATE_STRATEGY

    content_type = factory.SubFactory("tests.factories.ContentTypeFactory")
    object_id = factory.Sequence(lambda n: n)
    user = factory.SubFactory("tests.factories.UserFactory")
    account = factory.SubFactory("tests.factories.AccountFactory")


class ContentTypeFactory(Factory):
    class Meta:
        model = "contenttypes.ContentType"
        strategy = factory.CREATE_STRATEGY
        django_get_or_create = ("app_label", "model")

    app_label = factory.LazyAttribute(lambda obj: "issues")
    model = factory.LazyAttribute(lambda obj: "Issue")


class AttachmentFactory(Factory):
    class Meta:
        model = "attachments.Attachment"
        strategy = factory.CREATE_STRATEGY

    owner = factory.SubFactory("tests.factories.UserFactory")
    account = factory.SubFactory("tests.factories.AccountFactory")
    content_type = factory.SubFactory("tests.factories.ContentTypeFactory")
    object_id = factory.Sequence(lambda n: n)
    attached_file = factory.django.FileField(data=b"File contents")
    name = factory.Sequence(lambda n: "Attachment {}".format(n))

class AccountAttachmentFactory(Factory):
    account = factory.SubFactory("tests.factories.AccountFactory")
    owner = factory.SubFactory("tests.factories.UserFactory")
    content_object = factory.SubFactory("tests.factories.AccountFactory")
    attached_file = factory.django.FileField(data=b"File contents")
    name = factory.Sequence(lambda n: "Account Attachment {}".format(n))

    class Meta:
        model = "attachments.Attachment"
        strategy = factory.CREATE_STRATEGY


class HistoryEntryFactory(Factory):
    class Meta:
        model = "history.HistoryEntry"
        strategy = factory.CREATE_STRATEGY

    type = 1



class Missing:
    pass


def create_membership(**kwargs):
    "Create a membership along with its dependencies"
    account = kwargs.pop("account", AccountFactory())

    defaults = {
        "account": account,
        "user": UserFactory.create(),
        "role": RoleFactory.create(account=account,
                                   permissions=list(map(lambda x: x[0], MEMBERS_PERMISSIONS)))
    }
    defaults.update(kwargs)

    return MembershipFactory.create(**defaults)


def create_invitation(**kwargs):
    "Create an invitation along with its dependencies"
    account = kwargs.pop("account", AccountFactory())

    defaults = {
        "account": account,
        "role": RoleFactory.create(account=account),
        "email": "invited-user@email.com",
        "token": "tokenvalue",
        "invited_by_id": account.owner.id
    }
    defaults.update(kwargs)

    return MembershipFactory.create(**defaults)


def create_account(**kwargs):
    "Create a account along with its dependencies"
    defaults = {}
    defaults.update(kwargs)

    account = AccountFactory.create(**defaults)
    account.save()

    return account


def create_user(**kwargs):
    "Create an user along with her dependencies"
    RoleFactory.create()
    return UserFactory.create(**kwargs)