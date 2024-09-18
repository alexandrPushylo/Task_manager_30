from dashboard.models import Technic, User, ApplicationToday, WorkDaySheet, ApplicationTechnic
from dashboard.services import technic_sheet as TECHNIC_SHEET_SERVICE
import dashboard.assets as ASSETS
from django.db.models import QuerySet

from logger import getLogger

log = getLogger(__name__)


def create_app_technic(**kwargs) -> ApplicationTechnic:
    try:
        application_technic = ApplicationTechnic.objects.create(**kwargs)
        return application_technic
    except ValueError:
        log.error("create_app_technic(): ValueError")


def get_app_technic(**kwargs) -> ApplicationTechnic:
    try:
        application_technic = ApplicationTechnic.objects.get(**kwargs)
        return application_technic
    except ApplicationTechnic.DoesNotExist:
        log.error('get_app_technic(): ApplicationTechnic.DoesNotExist')


def get_apps_technic_queryset(select_related: tuple = (),
                              order_by: tuple = (),
                              exclude: tuple = (),
                              **kwargs) -> QuerySet[ApplicationTechnic]:
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


def reject_or_accept_apps_technic(app_tech_id) -> str | None:
    """
    Отвергнуть заявку
    :param app_tech_id:
    :return: reject | accept
    """
    apps_technic = get_app_technic(pk=app_tech_id)
    if apps_technic:
        if apps_technic.is_cancelled:
            apps_technic.isChecked = False
            apps_technic.is_cancelled = False
            apps_technic.description = apps_technic.description.replace(ASSETS.MessagesAssets.reject.value, "")
            apps_technic.technic_sheet.increment_count_application()
            apps_technic.save()
            return 'accept'
        else:
            apps_technic.isChecked = False
            apps_technic.is_cancelled = True
            apps_technic.description = ASSETS.MessagesAssets.reject.value + apps_technic.description
            apps_technic.technic_sheet.decrement_count_application()
            apps_technic.save()
            return 'reject'
    return None


def delete_application_technic(application_technic_id) -> str | None:
    """
    Удалить application_technic по "application_technic_id"
    :param application_technic_id:
    :return:
    """
    application_technic = get_app_technic(pk=application_technic_id)
    if application_technic:
        # TECHNIC_SHEET_SERVICE.calculate_count_applications(application_technic.technic_sheet.id)
        application_technic.technic_sheet.decrement_count_application()
        application_technic.delete()
        return 'success'
    return None
