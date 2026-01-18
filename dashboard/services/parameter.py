import enum

from dashboard.models import Parameter
from dashboard import variables as VAR
from django.db.models import QuerySet  # type: ignore

from dashboard.schemas.parameter_schema import ParameterSchema, SetParameterSchema
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
        cls.auto_create_global_parameters(global_parameters=parameters_list)


