from dataclasses import dataclass
from datetime import date

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from backend.plan.constants import FACTORY_MANAGER_GROUP, FACTORY_REPRESENTATIVE_GROUP
from backend.plan.exceptions import FactoryNotFoundError
from backend.plan.models import Factory, FactoryUser, WorkVolume, WorkVolumeRecord


@dataclass(frozen=True)
class WorkVolumeData:
    factory: int
    start: date
    finish: date
    weight: int
    author: int


def save_work_volume(data: WorkVolumeData) -> WorkVolume:
    factory = Factory.objects.filter(pk=data.factory).first()
    if factory is None:
        raise FactoryNotFoundError

    if not can_save_work_volume(data.author, factory):
        raise FactoryNotFoundError

    created = timezone.localdate()
    with transaction.atomic():
        work_volume, _ = WorkVolume.objects.update_or_create(
            factory=factory,
            start=data.start,
            finish=data.finish,
            defaults={"weight": data.weight, "created": created},
        )
        WorkVolumeRecord.objects.create(
            factory=factory.external_id,
            start=data.start,
            finish=data.finish,
            weight=data.weight,
            author=data.author,
            created=created,
        )
    return work_volume


def can_save_work_volume(author: int, factory: Factory) -> bool:
    user = get_user_model().objects.filter(pk=author, is_active=True).first()
    if user is None:
        return False

    group_names = set(user.groups.values_list("name", flat=True))
    if FACTORY_REPRESENTATIVE_GROUP in group_names:
        return FactoryUser.objects.filter(user=user, factory=factory).exists()
    return FACTORY_MANAGER_GROUP in group_names
