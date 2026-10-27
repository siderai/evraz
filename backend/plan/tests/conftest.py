import freezegun
import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from factory import Sequence, SubFactory
from factory.django import DjangoModelFactory
from rest_framework.test import APIClient

from backend.plan.constants import FACTORY_MANAGER_GROUP, FACTORY_REPRESENTATIVE_GROUP
from backend.plan.models import Factory, FactoryUser

freezegun.configure(extend_ignore_list=["clickhouse_backend"])


class UserFactory(DjangoModelFactory):
    class Meta:
        model = get_user_model()

    username = Sequence(lambda n: f"user-{n}")


class FactoryFactory(DjangoModelFactory):
    class Meta:
        model = Factory

    name = Sequence(lambda n: f"ЗМК {n}")


class FactoryUserFactory(DjangoModelFactory):
    class Meta:
        model = FactoryUser

    user = SubFactory(UserFactory)
    factory = SubFactory(FactoryFactory)


def user_in_group(group_name):
    user = UserFactory()
    user.groups.add(Group.objects.get_or_create(name=group_name)[0])
    return user


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def north():
    return FactoryFactory(name="ЗМК Северный")


@pytest.fixture
def south():
    return FactoryFactory(name="ЗМК Южный")


@pytest.fixture
def manager():
    return user_in_group(FACTORY_MANAGER_GROUP)


@pytest.fixture
def representative(north):
    user = user_in_group(FACTORY_REPRESENTATIVE_GROUP)
    FactoryUserFactory(user=user, factory=north)
    return user


@pytest.fixture
def outsider():
    return UserFactory()
