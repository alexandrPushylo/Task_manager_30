from dashboard.models import Technic, User, ApplicationToday, WorkDaySheet, ApplicationMaterial
import dashboard.assets as ASSETS

from logger import getLogger

log = getLogger(__name__)


def get_app_material(**kwargs) -> ApplicationMaterial | None:
    try:
        application_material = ApplicationMaterial.objects.get(**kwargs)
        return application_material
    except ApplicationMaterial.DoesNotExist:
        log.error("get_app_material(): ApplicationMaterial.DoesNotExist")
        return None


def get_apps_material_queryset(select_related: tuple = (),
                               order_by: tuple = (),
                               exclude: tuple = (),
                               **kwargs) -> ApplicationMaterial.objects:
    """
    :param exclude:
    :param order_by:
    :param select_related:
    :param kwargs: ApplicationMaterial.objects.filter(**kwargs)
    :return: ApplicationMaterial.objects.filter
    """

    apps_material = ApplicationMaterial.objects.filter(**kwargs)

    if select_related:
        apps_material = apps_material.select_related(*select_related)
    if order_by:
        apps_material = apps_material.order_by(*order_by)
    if exclude:
        apps_material = apps_material.exclude(*exclude)

    return apps_material
