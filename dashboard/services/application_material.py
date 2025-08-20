from dashboard.models import Technic, User, ApplicationToday, WorkDaySheet, ApplicationMaterial
from django.db.models import QuerySet  # type: ignore
import dashboard.assets as ASSETS

from logger import getLogger

log = getLogger(__name__)


def get_app_material(**kwargs) -> ApplicationMaterial | None:
    try:
        application_material = ApplicationMaterial.objects.get(**kwargs)
        return application_material
    except ApplicationMaterial.DoesNotExist:
        log.warning(f"get_app_material({kwargs}): ApplicationMaterial.DoesNotExist")
        return None


def create_app_material(**kwargs) -> ApplicationMaterial | None:
    try:
        application_material = ApplicationMaterial.objects.create(**kwargs)
        return application_material
    except ValueError:
        log.error(f"create_app_material({kwargs}): ValueError")
        return None


def get_apps_material_queryset(select_related: tuple = (),
                               order_by: tuple = (),
                               exclude: tuple = (),
                               **kwargs) -> QuerySet[ApplicationMaterial]:
    """
    :param exclude:
    :param order_by:
    :param select_related:
    :param kwargs: ApplicationMaterial.objects.filter(**kwargs)
    :return: QuerySet[ApplicationMaterial]
    """

    apps_material = ApplicationMaterial.objects.filter(**kwargs)

    if select_related:
        apps_material = apps_material.select_related(*select_related)
    if order_by:
        apps_material = apps_material.order_by(*order_by)
    if exclude:
        apps_material = apps_material.exclude(*exclude)

    return apps_material
