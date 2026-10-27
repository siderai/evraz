from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from backend.plan.exceptions import InvalidRequestError
from backend.plan.serializers import ErrorSerializer, ValidationErrorSerializer, WorkVolumeRequestSerializer
from backend.plan.services import WorkVolumeData, save_work_volume


class WorkVolumeListView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(
        operation_id="save_work_volume",
        summary="Сохранить объем работ",
        description=(
            "Сохраняет объем работ ЗМК за период в taDB и добавляет запись объема работ в tsDB. "
            "Даты передаются целым числом секунд Unix-времени (UTC)."
        ),
        request=WorkVolumeRequestSerializer,
        responses={
            status.HTTP_201_CREATED: OpenApiResponse(description="Объем работ сохранен"),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                ErrorSerializer,
                description="ЗМК не существует либо недоступен пользователю",
            ),
            status.HTTP_406_NOT_ACCEPTABLE: OpenApiResponse(
                ValidationErrorSerializer,
                description="Обязательные поля не заполнены либо значения некорректны",
            ),
        },
        examples=[
            OpenApiExample(
                "Объем работ за октябрь",
                value={
                    "factory": 1,
                    "start": 1790812800,
                    "finish": 1793404800,
                    "weight": 120000,
                    "author": 2,
                },
                request_only=True,
            ),
            OpenApiExample(
                "ЗМК недоступен",
                value={"errorCode": 174, "detail": "ЗМК не существует"},
                response_only=True,
                status_codes=["404"],
            ),
            OpenApiExample(
                "Поля не заполнены",
                value={
                    "errorCode": 279,
                    "detail": "Некорректные данные запроса",
                    "errors": {"start": ["Обязательное поле."]},
                },
                response_only=True,
                status_codes=["406"],
            ),
        ],
    )
    def post(self, request: Request) -> Response:
        serializer = WorkVolumeRequestSerializer(data=request.data)
        if not serializer.is_valid():
            raise InvalidRequestError(serializer.errors)

        save_work_volume(WorkVolumeData(**serializer.validated_data))

        return Response(status=status.HTTP_201_CREATED)
