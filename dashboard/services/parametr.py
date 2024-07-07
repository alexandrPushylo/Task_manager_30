from dashboard.models import Parameter
import dashboard.assets as ASSETS
import dashboard.variables as V
from django.db.models import QuerySet

from logger import getLogger

log = getLogger(__name__)


def get_parameter(**kwargs) -> Parameter:
    try:
        parameter = Parameter.objects.get(**kwargs)
        return parameter
    except Parameter.DoesNotExist:
        log.error(f'get_parameter(): DoesNotExist')


def get_parameter_queryset(select_related: tuple = (),
                           order_by: tuple = (),
                           **kwargs) -> QuerySet[Parameter]:
    parameter = Parameter.objects.filter(**kwargs)
    if select_related:
        parameter = parameter.select_related(*select_related)
    if order_by:
        parameter = parameter.order_by(*order_by)
    return parameter


def get_or_create_parameter(**kwargs) -> Parameter:
    parameter = get_parameter(**kwargs)
    if parameter:
        return parameter
    else:
        parameter = Parameter.objects.create(**kwargs)
        return parameter


def prepare_global_parameters(global_parameters: list[dict] = V.VARIABLES_LIST):
    if global_parameters:
        for item in global_parameters:
            parameter = Parameter.objects.filter(name=item['name'])
            if not parameter.exclude():
                Parameter.objects.create(
                    name=item.get('name'),
                    title=item.get('title'),
                    value=item.get('value'),
                    flag=item.get('flag', False),
                    description=item.get('description'),
                    time=item.get('time'),
                    date=item.get('date'),
                    permissions=item.get('permissions')
                )


def set_parameters(request_data: dict):
    if request_data:
        parameter_name_list = request_data.getlist('parameters_name')
        for parameter_name in parameter_name_list:
            parameter_name = str(parameter_name).strip()
            parameter = get_parameter(name=parameter_name)
            if parameter:
                value = request_data.get(f'{parameter_name}__value')
                flag = request_data.get(f'{parameter_name}__flag', False)
                time = request_data.get(f'{parameter_name}__time')
                date = request_data.get(f'{parameter_name}__date')
                description = request_data.get(f'{parameter_name}__description')

                parameter.value = value
                parameter.flag = bool(flag)
                parameter.time = time
                parameter.date = date
                parameter.description = description
                parameter.save()



