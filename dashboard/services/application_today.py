import enum
from typing import Literal

from django.db.models import QuerySet  # type: ignore

import dashboard.assets as ASSETS
import dashboard.utilities as utils
import dashboard.services.application_material as APP_MATERIAL_SERVICE
import dashboard.services.application_technic as APP_TECHNIC_SERVICE
import dashboard.services.technic_sheet as TECHNIC_SHEET_SERVICE
import dashboard.services.user as USERS_SERVICE
from dashboard.models import User, ApplicationToday
from dashboard.schemas.application_today_schema import (
    ApplicationTodaySchema,
    CreateApplicationTodaySchema,
)
from dashboard.services.base import BaseService
from logger import getLogger

log = getLogger(__name__)


class ApplicationTodayService(BaseService):
    model = ApplicationToday
    schema = ApplicationTodaySchema
    CACHE_TTL = 10

    class CacheKeys(enum.Enum):
        pass

    @classmethod
    def get_object(cls, *args, **kwargs) -> ApplicationToday | None:
        try:
            obj = cls.model.objects.get(*args, **kwargs)
            return obj
        except cls.model.DoesNotExist:
            log.warning(f"get_object({kwargs}): ApplicationToday.DoesNotExist ")
            return None
        except ValueError:
            log.warning(f"get_object({kwargs}): ValueError")
            return None

    @classmethod
    def get_queryset(cls, *args, **kwargs) -> QuerySet[ApplicationToday]:
        try:
            queryset = cls.model.objects.filter(*args, **kwargs)
            return queryset
        except ValueError:
            log.warning(f"get_queryset({kwargs}): ValueError")
            return cls.model.objects.none()

    @classmethod
    def get_or_create_by_data(cls, data: CreateApplicationTodaySchema) -> ApplicationToday | None:
        """
        Создать объект ApplicationToday
        :param data:
        :return: объект ApplicationToday
        """
        try:
            at, created = ApplicationToday.objects.get_or_create(
                construction_site_id=data.construction_site_id,
                date_id=data.date_id
            )
            if not created:
                if at.isArchive:
                    at.delete()
                    return cls.model.objects.create(
                        construction_site_id=data.construction_site_id,
                        date_id=data.date_id
                    )
            return at
        except ValueError:
            log.error(f"get_or_create_app_today(): ValueError")
            return None

    @classmethod
    def get_or_create(cls, *args, **kwargs) -> tuple[ApplicationToday, bool]:
        (obj, created) = cls.model.objects.get_or_create(*args, **kwargs)
        return obj, created

    @classmethod
    def delete(cls, **kwargs) -> ApplicationToday | None:
        at = cls.get_object(**kwargs)
        if at:
            at.isArchive = True
            at.status = ASSETS.ApplicationTodayStatus.DELETED.title
            at.save(update_fields=['status', 'isArchive'])
            return at
        return None

    @classmethod
    def restore(
            cls,
            status: Literal["deleted", "absent", "saved", "submitted", "approved", "send"],
            **kwargs
    ) -> ApplicationToday | None:
        at = cls.get_object(**kwargs)
        if at:
            at.isArchive = False
            at.status = status
            at.save(update_fields=['status', 'isArchive'])
            return at
        return None


# def get_apps_today(**kwargs) -> ApplicationToday | None:
#     try:
#         application_today = ApplicationToday.objects.get(**kwargs)
#         return application_today
#     except ApplicationToday.DoesNotExist:
#         log.warning(f"get_apps_today({kwargs}): ApplicationToday.DoesNotExist")
#         return None
#     except ApplicationToday.MultipleObjectsReturned:
#         log.error(f"get_apps_today({kwargs}): ApplicationToday.MultipleObjectsReturned")
#         return None
#     except ValueError:
#         log.error(f"get_apps_today({kwargs}): ValueError")
#         return None


# def create_app_today(**kwargs) -> ApplicationToday | None:
#     """
#     Создать объект ApplicationToday
#     :param kwargs:
#     :return: объект ApplicationToday
#     """
#     try:
#         application_today, created = ApplicationToday.objects.get_or_create(**kwargs)
#         if not created:
#             if application_today.isArchive:
#                 application_today.delete()
#                 return ApplicationToday.objects.create(**kwargs)
#
#         return application_today
#     except ValueError:
#         log.error(f"get_or_create_app_today({kwargs}): ValueError")
#         return None


# def get_apps_today_queryset(select_related: tuple = (),
#                             order_by: tuple = (),
#                             **kwargs) -> QuerySet[ApplicationToday]:
#     """
#     :param order_by:
#     :param select_related:
#     :param kwargs: ApplicationToday.objects.filter(**kwargs)
#     :return: ApplicationToday.objects.filter
#     """
#
#     apps_today = ApplicationToday.objects.filter(**kwargs)
#
#     if select_related:
#         apps_today = apps_today.select_related(*select_related)
#     if order_by:
#         apps_today = apps_today.order_by(*order_by)
#     return apps_today


# def get_default_status_for_apps_today(
#         user: User
# ) -> Literal["deleted", "absent", "saved", "submitted", "approved", "send"]:
#     if USERS_SERVICE.is_administrator(user):
#         return ASSETS.ApplicationTodayStatus.SUBMITTED.title
#     elif USERS_SERVICE.is_mechanic(user):
#         return ASSETS.ApplicationTodayStatus.SUBMITTED.title
#     else:
#         return ASSETS.ApplicationTodayStatus.SAVED.title


# def delete_application_today(application_today: ApplicationToday):
#     """
#     Удалить application_today: ApplicationToday и деинкрементировать technic_sheet
#     :param application_today:
#     :return:
#     """
#     technic_sheet_id_list = APP_TECHNIC_SERVICE.get_apps_technic_queryset(
#         isArchive=False,
#         application_today=application_today
#         ).values_list('technic_sheet', flat=True)
#
#     # TECHNIC_SHEET_SERVICE.decrement_technic_sheet_list(technic_sheet_id_list, exclude_app_tech=application_today.id)
#     utils.calculate_all_app_for_technic_sheet(
#         list(technic_sheet_id_list),
#         exclude_app_tech_list=application_today.id
#     )
#
#     application_today.isArchive = True
#     application_today.status = ASSETS.ApplicationTodayStatus.DELETED.title
#     application_today.save(update_fields=['isArchive', 'status'])


# def restore_application_today(application_today: ApplicationToday, status: str):
#     """
#     Восстановить application_today: ApplicationToday и деинкрементировать technic_sheet
#     :param status:
#     :param application_today:
#     :return:
#     """
#     technic_sheet_id_list = APP_TECHNIC_SERVICE.get_apps_technic_queryset(
#         isArchive=False,
#         application_today=application_today
#         ).values_list('technic_sheet', flat=True)
#     # TECHNIC_SHEET_SERVICE.decrement_technic_sheet_list(technic_sheet_id_list)
#     utils.calculate_all_app_for_technic_sheet(list(technic_sheet_id_list))
#     application_today.isArchive = False
#     application_today.status = status
#     application_today.save(update_fields=['isArchive', 'status'])


# def validate_application_today(
#         application_today: ApplicationToday,
#         default_status: str | None = None
# ) -> bool:
#     """
#     Проверка application_today: ApplicationToday
#     :param application_today: application_today: ApplicationToday
#     :param default_status: save or submitted
#     :return: True if application_today is valid and save, else False and delete
#     """
#     app_today_description = application_today.description is not None and application_today.description != ''
#     app_technic = APP_TECHNIC_SERVICE.get_apps_technic_queryset(
#         application_today=application_today,
#         isArchive=False,
#     ).exists()
#     app_material = APP_MATERIAL_SERVICE.get_apps_material_queryset(
#         application_today=application_today,
#         isArchive=False,
#     ).exists()
#     if any((app_today_description, app_technic, app_material)):
#         if application_today.is_edited and default_status:
#             application_today.status = default_status
#             application_today.is_edited = False
#         application_today.save()
#         return True
#     else:
#         application_today.delete()
#         return False
