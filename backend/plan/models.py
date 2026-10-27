import uuid

from clickhouse_backend import models as clickhouse_models
from django.conf import settings
from django.db import models


class Factory(models.Model):
    external_id = models.UUIDField("внешний идентификатор", default=uuid.uuid4, unique=True, editable=False)
    name = models.CharField("название", max_length=255)
    users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through="plan.FactoryUser",
        related_name="factories",
        verbose_name="пользователи",
    )

    class Meta:
        verbose_name = "ЗМК"
        verbose_name_plural = "ЗМК"
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name


class FactoryUser(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="factory_users",
        verbose_name="пользователь",
    )
    factory = models.ForeignKey(Factory, on_delete=models.CASCADE, related_name="factory_users", verbose_name="ЗМК")

    class Meta:
        verbose_name = "пользователь завода"
        verbose_name_plural = "пользователи завода"
        ordering = ("factory", "user")
        constraints = (models.UniqueConstraint(fields=("user", "factory"), name="unique_factory_user"),)

    def __str__(self) -> str:
        return f"{self.user} — {self.factory}"


class WorkVolume(models.Model):
    factory = models.ForeignKey(Factory, on_delete=models.CASCADE, related_name="work_volumes", verbose_name="ЗМК")
    start = models.DateField("начальная дата")
    finish = models.DateField("конечная дата")
    weight = models.PositiveIntegerField("вес, кг")
    created = models.DateField("дата создания")

    class Meta:
        verbose_name = "объем работы"
        verbose_name_plural = "объемы работ"
        ordering = ("factory", "start", "finish")
        constraints = (
            models.UniqueConstraint(fields=("factory", "start", "finish"), name="unique_work_volume_period"),
        )

    def __str__(self) -> str:
        return f"{self.factory}: {self.start} — {self.finish}"


class WorkVolumeRecord(clickhouse_models.ClickhouseModel):
    factory = clickhouse_models.UUIDField("внешний идентификатор ЗМК")
    start = clickhouse_models.Date32Field("начальная дата")
    finish = clickhouse_models.Date32Field("конечная дата")
    weight = clickhouse_models.Int64Field("вес, кг")
    author = clickhouse_models.Int64Field("автор записи")
    created = clickhouse_models.Date32Field("дата создания")

    class Meta:
        verbose_name = "запись объема работы"
        verbose_name_plural = "записи объемов работ"
        ordering = ("-created", "-id")
        engine = clickhouse_models.MergeTree(
            order_by=("created", "factory", "id"),
            partition_by=clickhouse_models.toYYYYMM("created"),
        )

    def __str__(self) -> str:
        return f"{self.factory}: {self.start} — {self.finish}"
