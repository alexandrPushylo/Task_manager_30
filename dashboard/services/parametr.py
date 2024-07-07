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


