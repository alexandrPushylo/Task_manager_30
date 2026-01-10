import enum

from django.core.handlers.wsgi import WSGIRequest

from dashboard.models import Parameter
from dashboard import variables as VAR
from django.db.models import QuerySet  # type: ignore

from dashboard.schemas.parameter_schema import ParameterSchema, CreateParameterSchema, SetParameterSchema
from dashboard.services.base import BaseService
from logger import getLogger

log = getLogger(__name__)


class ParameterService(BaseService):
    model = Parameter
    schema = ParameterSchema
    CACHE_TTL = 10

    class CacheKeys(enum.Enum):
        pass

    @classmethod
    def get_object(cls, *args, **kwargs) -> Parameter | None:
        try:
            obj = cls.model.objects.get(*args, **kwargs)
            return obj
        except cls.model.DoesNotExist:
            log.warning(f"get_object({kwargs}): Parameter.DoesNotExist ")
            return None
        except ValueError:
            log.warning(f"get_object({kwargs}): ValueError")
            return None

    @classmethod
    def get_queryset(cls, *args, **kwargs) -> QuerySet[Parameter]:
        try:
            queryset = cls.model.objects.filter(*args, **kwargs)
            return queryset
        except ValueError:
            log.warning(f"get_queryset({kwargs}): ValueError")
            return cls.model.objects.none()

    @classmethod
    def is_exist(cls, **kwargs) -> bool:
        pr = cls.get_queryset(**kwargs)
        return pr.exists()

    @classmethod
    def get_or_create(cls, *args, **kwargs) -> Parameter | None:
        parameter = cls.get_object(**kwargs)
        if parameter:
            return parameter
        else:
            parameter = Parameter.objects.create(**kwargs)
            return parameter

    @classmethod
    def auto_create_global_parameters(cls, global_parameters: list[dict]):
        """
        Авто создание переменных
        :param global_parameters:
        :return:
        """

        parameters = global_parameters
        if parameters:
            for item in parameters:
                pr__is_exist = cls.is_exist(name=item["name"])
                if not pr__is_exist:
                    cls.model.objects.create(
                        name=item["name"],
                        title=item["title"],
                        value=item["value"],
                        flag=item["flag"],
                        description=item["description"],
                        time=item["time"],
                        date=item["date"],
                        permissions=item["permissions"],
                    )

    @classmethod
    def set_parameters(cls, parameter_list: list[SetParameterSchema]):
        if parameter_list:
            for pr_data in parameter_list:
                parameter = cls.get_object(name=pr_data.name)
                if parameter:
                    parameter.value = pr_data.value
                    parameter.flag = pr_data.flag
                    parameter.time = pr_data.time
                    parameter.date = pr_data.date
                    parameter.description = pr_data.description
                    parameter.save()

    @classmethod
    def get_parameter_for_supply(cls) -> QuerySet[Parameter]:
        pr = cls.get_queryset(title=VAR.VAR_TIME_RECEPTION_OF_MATERIALS['title'])
        if pr:
            return pr
        return cls.model.objects.none()

    @classmethod
    def prepare_global_parameters(cls):
        """
        Авто создание переменных
        :return:
        """
        parameters_list = VAR.VARIABLES_LIST
        # PARAMETER_SERVICE.create_global_parameters(global_parameters=parameters_list)
        cls.auto_create_global_parameters(global_parameters=parameters_list)


# def get_parameter(**kwargs) -> Parameter:
#     try:
#         parameter = Parameter.objects.get(**kwargs)
#         return parameter
#     except Parameter.DoesNotExist:
#         log.error(f'get_parameter({kwargs}): DoesNotExist')
#         return Parameter.objects.none()
#
#
# def get_parameter_queryset(select_related: tuple = (),
#                            order_by: tuple = (),
#                            **kwargs) -> QuerySet[Parameter]:
#     parameter = Parameter.objects.filter(**kwargs)
#     if select_related:
#         parameter = parameter.select_related(*select_related)
#     if order_by:
#         parameter = parameter.order_by(*order_by)
#     return parameter


# def get_or_create_parameter(**kwargs) -> Parameter:
#     parameter = get_parameter(**kwargs)
#     if parameter:
#         return parameter
#     else:
#         parameter = Parameter.objects.create(**kwargs)
#         return parameter


# def create_global_parameters(global_parameters: list[dict]):
#     """
#     Авто создание переменных
#     :param global_parameters:
#     :return:
#     """
#     if global_parameters:
#         for item in global_parameters:
#             parameter = Parameter.objects.filter(name=item['name'])
#             if not parameter.exclude():
#                 Parameter.objects.create(
#                     name=item.get('name'),
#                     title=item.get('title'),
#                     value=item.get('value'),
#                     flag=item.get('flag', False),
#                     description=item.get('description'),
#                     time=item.get('time'),
#                     date=item.get('date'),
#                     permissions=item.get('permissions')
#                 )


# def set_parameters(request_data: WSGIRequest.POST):
#     if request_data:
#         parameter_name_list = request_data.getlist('parameters_name')
#         for parameter_name in parameter_name_list:
#             parameter_name = str(parameter_name).strip()
#             parameter = get_parameter(name=parameter_name)
#             if parameter:
#                 value = request_data.get(f'{parameter_name}__value')
#                 flag = request_data.get(f'{parameter_name}__flag', False)
#                 time = request_data.get(f'{parameter_name}__time')
#                 date = request_data.get(f'{parameter_name}__date')
#                 description = request_data.get(f'{parameter_name}__description')
#
#                 parameter.value = value
#                 parameter.flag = bool(flag)
#                 parameter.time = time
#                 parameter.date = date
#                 parameter.description = description
#                 parameter.save()


# def get_parameters_for_supply() -> QuerySet[Parameter]:
#     """
#     Получить параметры для supply
#     :return:
#     """
#     parameters_list = get_parameter_queryset(
#         title=VAR.VAR_TIME_RECEPTION_OF_MATERIALS['title']
#     )
#     return parameters_list
