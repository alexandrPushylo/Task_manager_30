from dashboard.models import Technic, User, ApplicationToday, WorkDaySheet, ApplicationTechnic
import dashboard.assets as ASSETS

from logger import getLogger

log = getLogger(__name__)


def get_app_technic(**kwargs) -> ApplicationTechnic | None:
    try:
        application_technic = ApplicationTechnic.objects.get(**kwargs)
        return application_technic
    except ApplicationTechnic.DoesNotExist:
        log.error('get_app_technic(): ApplicationTechnic.DoesNotExist')
        return None


def get_apps_technic_queryset(select_related: tuple = (),
                              order_by: tuple = (),
                              exclude: tuple = (),
                              **kwargs) -> ApplicationTechnic.objects:
    """
    :param exclude:
    :param order_by:
    :param select_related:
    :param kwargs: ApplicationTechnic.objects.filter(**kwargs)
    :return: ApplicationTechnic.objects.filter
    """

    apps_technic = ApplicationTechnic.objects.filter(**kwargs)

    if select_related:
        apps_technic = apps_technic.select_related(*select_related)
    if order_by:
        apps_technic = apps_technic.order_by(*order_by)
    if exclude:
        apps_technic = apps_technic.exclude(*exclude)

    return apps_technic


def toggle_reject_apps_technic(app_tech_id) -> None:
    """
    Отвергнуть заявку
    :param app_tech_id:
    :return:
    """
    apps_technic = get_app_technic(pk=app_tech_id)
    if apps_technic:
        if apps_technic.is_cancelled:
            apps_technic.isChecked = False
            apps_technic.is_cancelled = False
            apps_technic.description = apps_technic.description.replace(ASSETS.MESSAGES['reject'], "")
            apps_technic.technic_sheet.increment_count_application()
            apps_technic.save()
        else:
            apps_technic.isChecked = False
            apps_technic.is_cancelled = True
            apps_technic.description = ASSETS.MESSAGES['reject'] + apps_technic.description
            apps_technic.technic_sheet.decrement_count_application()
            apps_technic.save()


