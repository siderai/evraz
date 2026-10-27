from datetime import UTC, date, datetime

from rest_framework import serializers


def date_from_timestamp(timestamp: int) -> date:
    try:
        return datetime.fromtimestamp(timestamp, tz=UTC).date()
    except (OSError, OverflowError, ValueError) as exc:
        raise serializers.ValidationError("Значение не является корректной датой.") from exc


class WorkVolumeRequestSerializer(serializers.Serializer):
    factory = serializers.IntegerField(help_text="Идентификатор ЗМК")
    start = serializers.IntegerField(help_text="Начальная дата периода, Unix-время в секундах (UTC)")
    finish = serializers.IntegerField(help_text="Конечная дата периода, Unix-время в секундах (UTC)")
    weight = serializers.IntegerField(min_value=0, help_text="Вес, кг")
    author = serializers.IntegerField(help_text="Идентификатор пользователя, сохраняющего объем работ")

    def validate_start(self, value: int) -> date:
        return date_from_timestamp(value)

    def validate_finish(self, value: int) -> date:
        return date_from_timestamp(value)


class ErrorSerializer(serializers.Serializer):
    errorCode = serializers.IntegerField(help_text="Код ошибки из спецификации")
    detail = serializers.CharField(help_text="Описание ошибки")


class ValidationErrorSerializer(ErrorSerializer):
    errors = serializers.DictField(
        child=serializers.ListField(child=serializers.CharField()),
        help_text="Ошибки по полям запроса",
    )
