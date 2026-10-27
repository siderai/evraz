import calendar
from datetime import date
from unittest import mock

import pytest
from django.contrib.auth import get_user_model
from freezegun import freeze_time

from backend.plan.models import WorkVolume, WorkVolumeRecord

pytestmark = pytest.mark.django_db(databases=("default", "tsdb"), transaction=True)

URL = "/work-volume-list/"
TODAY = date(2026, 5, 20)
LATER = date(2026, 5, 21)
START = date(2026, 10, 1)
FINISH = date(2026, 10, 31)


def timestamp(value):
    return calendar.timegm(value.timetuple())


def payload(factory, author, start=START, finish=FINISH, weight=120000):
    return {
        "factory": factory,
        "start": timestamp(start),
        "finish": timestamp(finish),
        "weight": weight,
        "author": author,
    }


@freeze_time(TODAY)
def test__post__saves_work_volume_and_record_when_manager(api_client, manager, north):
    """Менеджер по взаимодействию с ЗМК сохраняет объем работ по ЗМК."""
    # act
    response = api_client.post(URL, payload(north.id, manager.id), format="json")

    # assert
    assert response.status_code == 201
    assert not response.content
    assert WorkVolume.objects.values().get() == {
        "id": mock.ANY,
        "factory_id": north.id,
        "start": START,
        "finish": FINISH,
        "weight": 120000,
        "created": TODAY,
    }
    assert WorkVolumeRecord.objects.values().get() == {
        "id": mock.ANY,
        "factory": north.external_id,
        "start": START,
        "finish": FINISH,
        "weight": 120000,
        "author": manager.id,
        "created": TODAY,
    }


@freeze_time(TODAY)
def test__post__saves_work_volume_when_representative_of_own_factory(api_client, representative, north):
    """Представитель ЗМК сохраняет объем работ по своему ЗМК."""
    # act
    response = api_client.post(URL, payload(north.id, representative.id), format="json")

    # assert
    assert response.status_code == 201
    assert WorkVolume.objects.filter(factory=north, weight=120000).exists()
    assert WorkVolumeRecord.objects.values().get()["author"] == representative.id


def test__post__replaces_weight_and_keeps_history_when_period_already_saved(api_client, manager, north):
    """Повторное сохранение объема работ за тот же период заменяет вес, а история сохранений пополняется."""
    # arrange
    with freeze_time(TODAY):
        api_client.post(URL, payload(north.id, manager.id, weight=120000), format="json")

    # act
    with freeze_time(LATER):
        response = api_client.post(URL, payload(north.id, manager.id, weight=150000), format="json")

    # assert
    assert response.status_code == 201
    assert WorkVolume.objects.values().get() == {
        "id": mock.ANY,
        "factory_id": north.id,
        "start": START,
        "finish": FINISH,
        "weight": 150000,
        "created": LATER,
    }
    assert list(WorkVolumeRecord.objects.order_by("created").values_list("weight", "created")) == [
        (120000, TODAY),
        (150000, LATER),
    ]


@freeze_time(TODAY)
def test__post__saves_separate_work_volumes_when_periods_differ(api_client, manager, north):
    """Объемы работ за разные периоды хранятся отдельно."""
    # arrange
    api_client.post(URL, payload(north.id, manager.id), format="json")

    # act
    response = api_client.post(
        URL,
        payload(north.id, manager.id, start=date(2026, 11, 1), finish=date(2026, 11, 30), weight=90000),
        format="json",
    )

    # assert
    assert response.status_code == 201
    assert list(WorkVolume.objects.order_by("start").values_list("start", "weight")) == [
        (START, 120000),
        (date(2026, 11, 1), 90000),
    ]


def test__post__returns_404_when_representative_of_another_factory(api_client, representative, south):
    """Представитель ЗМК не может сохранить объем работ по чужому ЗМК."""
    # act
    response = api_client.post(URL, payload(south.id, representative.id), format="json")

    # assert
    assert response.status_code == 404
    assert response.json() == {"errorCode": 174, "detail": "ЗМК не существует"}
    assert not WorkVolume.objects.exists()
    assert not WorkVolumeRecord.objects.exists()


@pytest.mark.parametrize("factory_id", [999999, 0])
def test__post__returns_404_when_factory_does_not_exist(api_client, manager, factory_id):
    """Объем работ по несуществующему ЗМК сохранить нельзя."""
    # act
    response = api_client.post(URL, payload(factory_id, manager.id), format="json")

    # assert
    assert response.status_code == 404
    assert response.json() == {"errorCode": 174, "detail": "ЗМК не существует"}


def test__post__returns_404_when_author_has_no_groups(api_client, outsider, north):
    """Пользователь без роли не может сохранить объем работ."""
    # act
    response = api_client.post(URL, payload(north.id, outsider.id), format="json")

    # assert
    assert response.status_code == 404
    assert response.json() == {"errorCode": 174, "detail": "ЗМК не существует"}
    assert not WorkVolume.objects.exists()


def test__post__returns_404_when_author_does_not_exist(api_client, north):
    """Объем работ от имени несуществующего пользователя не сохраняется."""
    # act
    response = api_client.post(URL, payload(north.id, 999999), format="json")

    # assert
    assert response.status_code == 404
    assert response.json() == {"errorCode": 174, "detail": "ЗМК не существует"}


def test__post__returns_404_when_author_is_blocked(api_client, manager, north):
    """Заблокированный пользователь не может сохранить объем работ."""
    # arrange
    get_user_model().objects.filter(pk=manager.pk).update(is_active=False)

    # act
    response = api_client.post(URL, payload(north.id, manager.id), format="json")

    # assert
    assert response.status_code == 404
    assert response.json() == {"errorCode": 174, "detail": "ЗМК не существует"}


@pytest.mark.parametrize("missing_field", ["factory", "start", "finish", "weight", "author"])
def test__post__returns_406_when_required_field_missing(api_client, manager, north, missing_field):
    """Без любого из обязательных полей объем работ не сохраняется."""
    # arrange
    body = payload(north.id, manager.id)
    body.pop(missing_field)

    # act
    response = api_client.post(URL, body, format="json")

    # assert
    assert response.status_code == 406
    assert response.json() == {
        "errorCode": 279,
        "detail": "Некорректные данные запроса",
        "errors": {missing_field: ["Обязательное поле."]},
    }
    assert not WorkVolume.objects.exists()
    assert not WorkVolumeRecord.objects.exists()


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("start", "не дата"),
        ("start", 100000000000000000000),
        ("finish", None),
        ("weight", -1),
    ],
)
def test__post__returns_406_when_field_value_is_invalid(api_client, manager, north, field, value):
    """Поле с некорректным значением не принимается."""
    # arrange
    body = payload(north.id, manager.id)
    body[field] = value

    # act
    response = api_client.post(URL, body, format="json")

    # assert
    assert response.status_code == 406
    assert response.json()["errorCode"] == 279
    assert field in response.json()["errors"]
    assert not WorkVolume.objects.exists()


def test__get__returns_405_when_method_is_not_post(api_client):
    """Объем работ можно только сохранять — читать список через этот адрес нельзя."""
    # act
    response = api_client.get(URL)

    # assert
    assert response.status_code == 405
