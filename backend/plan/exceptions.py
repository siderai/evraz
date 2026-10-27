from typing import Any

from rest_framework import status
from rest_framework.exceptions import APIException


class PlanAPIError(APIException):
    error_code: int

    def __init__(self, errors: Any = None) -> None:
        self.detail = {"errorCode": self.error_code, "detail": self.default_detail}
        if errors is not None:
            self.detail["errors"] = errors


class FactoryNotFoundError(PlanAPIError):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "ЗМК не существует"
    error_code = 174


class InvalidRequestError(PlanAPIError):
    status_code = status.HTTP_406_NOT_ACCEPTABLE
    default_detail = "Некорректные данные запроса"
    error_code = 279
