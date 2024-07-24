from django.db.models import QuerySet  # type: ignore

import dashboard.assets as ASSETS
import dashboard.services.application_material as APP_MATERIAL_SERVICE
import dashboard.services.application_technic as APP_TECHNIC_SERVICE
import dashboard.services.technic_sheet as TECHNIC_SHEET_SERVICE
import dashboard.services.user as USERS_SERVICE
from dashboard.models import User, ApplicationToday
from logger import getLogger

log = getLogger(__name__)


def get_apps_today(**kwargs) -> ApplicationToday:
    try:
        application_today = ApplicationToday.objects.get(**kwargs)
        return application_today
    except ApplicationToday.DoesNotExist:
        log.warning("get_apps_today(): ApplicationToday.DoesNotExist")
        return ApplicationToday.objects.none()
    except ValueError:
        log.error("get_apps_today(): ValueError")
        return ApplicationToday.objects.none()


def create_app_today(**kwargs) -> ApplicationToday:
    """
    Создать объект ApplicationToday
    :param kwargs:
    :return: объект ApplicationToday
    """
    try:
        application_today = ApplicationToday.objects.create(**kwargs)
        return application_today
    except ValueError:
        log.error("get_or_create_app_today(): ValueError")
        return ApplicationToday.objects.none()


def get_apps_today_queryset(select_related: tuple = (),
                            order_by: tuple = (),
                            **kwargs) -> QuerySet[ApplicationToday]:
    """
    :param order_by:
    :param select_related:
    :param kwargs: ApplicationToday.objects.filter(**kwargs)
    :return: ApplicationToday.objects.filter
    """

    apps_today = ApplicationToday.objects.filter(**kwargs)

    if select_related:
        apps_today = apps_today.select_related(*select_related)
    if order_by:
        apps_today = apps_today.order_by(*order_by)
    return apps_today


def get_default_status_for_apps_today(user: User) -> str:
    if USERS_SERVICE.is_administrator(user):
        return ASSETS.ApplicationTodayStatus.SUBMITTED.title
    else:
        return ASSETS.ApplicationTodayStatus.SAVED.title


def delete_application_today(application_today: ApplicationToday):
    """
    Удалить application_today: ApplicationToday и деинкрементировать technic_sheet
    :param application_today:
    :return:
    """
    technic_sheet_id_list = APP_TECHNIC_SERVICE.get_apps_technic_queryset(
        isArchive=False, application_today=application_today
    ).values_list('technic_sheet', flat=True)
    TECHNIC_SHEET_SERVICE.decrement_technic_sheet_list(technic_sheet_id_list)
    application_today.delete()


def validate_application_today(application_today: ApplicationToday, default_status: str | None = None) -> bool:
    """
    Проверка application_today: ApplicationToday
    :param application_today: application_today: ApplicationToday
    :param default_status: save or submitted
    :return: True if application_today is valid and save, else False and delete
    """
    app_today_description = application_today.description is not None and application_today.description != ''
    app_technic = APP_TECHNIC_SERVICE.get_apps_technic_queryset(application_today=application_today).exists()
    app_material = APP_MATERIAL_SERVICE.get_apps_material_queryset(application_today=application_today).exists()
    if any((app_today_description, app_technic, app_material)):
        if application_today.is_edited and default_status:
            application_today.status = default_status
            application_today.is_edited = False
        application_today.save()
        return True
    else:
        application_today.delete()
        return False

