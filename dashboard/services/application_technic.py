import enum
from typing import Literal

from dashboard.models import ApplicationTechnic

from django.db.models import QuerySet

from dashboard.schemas.application_technic_schema import (
    ApplicationTechnicSchema,
    EditApplicationTechnicSchema,
)
from dashboard.services.base import BaseService
from logger import getLogger

log = getLogger(__name__)


class EditApplicationTechnic:
    pass


class ApplicationTechnicService(BaseService):
    model = ApplicationTechnic
    schema = ApplicationTechnicSchema
    CACHE_TTL = 10

    class CacheKeys(enum.Enum):
        pass

    @classmethod
    def get_object(cls, *args, **kwargs) -> ApplicationTechnic | None:
        try:
            obj = cls.model.objects.get(*args, **kwargs)
            return obj
        except cls.model.DoesNotExist:
            log.warning(f"get_object({kwargs}): ApplicationTechnic.DoesNotExist ")
            return None
        except ValueError:
            log.warning(f"get_object({kwargs}): ValueError")
            return None

    @classmethod
    def get_queryset(cls, *args, **kwargs) -> QuerySet[ApplicationTechnic]:
        try:
            queryset = cls.model.objects.filter(*args, **kwargs)
            return queryset
        except ValueError:
            log.warning(f"get_queryset({kwargs}): ValueError")
            return cls.model.objects.none()

    @classmethod
    def create(
            cls,
            app_technic_data: EditApplicationTechnicSchema
    ) -> ApplicationTechnic | None:
        try:
            am = cls.model.objects.create(**app_technic_data.model_dump())
            return am
        except ValueError:
            log.warning(f"create_application_technic(): ValueError")
            return None

    @classmethod
    def delete(cls, *args, **kwargs) -> Literal["success"] | None:
        """
        Удалить application_technic по "application_technic_id"
        :return:
        """
        at = cls.get_object(*args, **kwargs)
        if at:
            if at.technic_sheet:
                at.technic_sheet.decrement_count_application()
            at.isArchive = True
            at.save(update_fields=["isArchive"])
            return 'success'
        return None

    @classmethod
    def get_or_create(cls, *args, **kwargs) -> tuple[ApplicationTechnic, bool]:
        (obj, created) = cls.model.objects.get_or_create(*args, **kwargs)
        return obj, created

    @classmethod
    def is_exist(cls, *args, **kwargs) -> bool:
        at = cls.get_queryset(*args, **kwargs)
        return at.exists()

    @classmethod
    def reject_or_accept(cls, app_technic_id: int) -> Literal["accept", "reject"] | None:
        """
        Отвергнуть заявку
        :param app_technic_id:
        :return: reject | accept
        """
        at = cls.get_object(id=app_technic_id)
        if at:
            if at.is_cancelled:
                at.isChecked = False
                at.is_cancelled = False
                at.technic_sheet.increment_count_application()
                at.save()
                return "accept"
            else:
                at.isChecked = False
                at.is_cancelled = True
                at.technic_sheet.decrement_count_application()
                at.save()
                return "reject"
        return None


# def create_app_technic(**kwargs) -> ApplicationTechnic:
#     try:
#         application_technic = ApplicationTechnic.objects.create(**kwargs)
#         return application_technic
#     except ValueError:
#         log.error(f"create_app_technic({kwargs}): ValueError")


# def get_app_technic(**kwargs) -> ApplicationTechnic:
#     try:
#         application_technic = ApplicationTechnic.objects.get(**kwargs)
#         return application_technic
#     except ApplicationTechnic.DoesNotExist:
#         log.warning(f'get_app_technic({kwargs}): ApplicationTechnic.DoesNotExist')


# def get_apps_technic_queryset(select_related: tuple = (),
#                               order_by: tuple = (),
#                               exclude: tuple = (),
#                               **kwargs) -> QuerySet[ApplicationTechnic]:
#     """
#     :param exclude:
#     :param order_by:
#     :param select_related:
#     :param kwargs: ApplicationTechnic.objects.filter(**kwargs)
#     :return: ApplicationTechnic.objects.filter
#     """
#
#     apps_technic = ApplicationTechnic.objects.filter(**kwargs)
#
#     if select_related:
#         apps_technic = apps_technic.select_related(*select_related)
#     if order_by:
#         apps_technic = apps_technic.order_by(*order_by)
#     if exclude:
#         apps_technic = apps_technic.exclude(*exclude)
#
#     return apps_technic


# def reject_or_accept_apps_technic(app_tech_id) -> str | None:
#     """
#     Отвергнуть заявку
#     :param app_tech_id:
#     :return: reject | accept
#     """
#     apps_technic = get_app_technic(pk=app_tech_id)
#     if apps_technic:
#         if apps_technic.is_cancelled:
#             apps_technic.isChecked = False
#             apps_technic.is_cancelled = False
#             apps_technic.technic_sheet.increment_count_application()
#             apps_technic.save()
#             return 'accept'
#         else:
#             apps_technic.isChecked = False
#             apps_technic.is_cancelled = True
#             apps_technic.technic_sheet.decrement_count_application()
#             apps_technic.save()
#             return 'reject'
#     return None


# def delete_application_technic(application_technic_id) -> str | None:
#     """
#     Удалить application_technic по "application_technic_id"
#     :param application_technic_id:
#     :return:
#     """
#     application_technic = get_app_technic(pk=application_technic_id)
#     if application_technic:
#         if application_technic.technic_sheet:
#             application_technic.technic_sheet.decrement_count_application()
#         # application_technic.delete()
#         application_technic.isArchive = True
#         application_technic.save(update_fields=['isArchive'])
#         return 'success'
#     return None
