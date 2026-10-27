from typing import Any

from clickhouse_backend.models import ClickhouseModel
from django.apps import apps
from django.db.models import Model

TIME_SERIES_DATABASE = "tsdb"


def is_time_series_model(model: type[Model] | None) -> bool:
    if model is None:
        return False
    if issubclass(model, ClickhouseModel):
        return True
    return getattr(model._meta, "engine", None) is not None


class ClickHouseRouter:
    def db_for_read(self, model: type[Model], **hints: Any) -> str | None:
        return TIME_SERIES_DATABASE if is_time_series_model(model) else None

    def db_for_write(self, model: type[Model], **hints: Any) -> str | None:
        return TIME_SERIES_DATABASE if is_time_series_model(model) else None

    def allow_relation(self, obj1: Model, obj2: Model, **hints: Any) -> bool | None:
        if is_time_series_model(type(obj1)) != is_time_series_model(type(obj2)):
            return False
        return None

    def allow_migrate(self, db: str, app_label: str, model_name: str | None = None, **hints: Any) -> bool | None:
        model = hints.get("model")
        if model_name is not None:
            try:
                model = apps.get_model(app_label, model_name)
            except LookupError:
                pass
        if is_time_series_model(model):
            return db == TIME_SERIES_DATABASE
        return db != TIME_SERIES_DATABASE
