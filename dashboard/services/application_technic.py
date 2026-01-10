import enum
from typing import Literal

from django.core.cache import cache

from dashboard.models import ApplicationTechnic

from django.db.models import QuerySet

from dashboard.schemas.application_technic_schema import (
    ApplicationTechnicSchema,
    EditApplicationTechnicSchema,
)
from dashboard.schemas.work_day_sheet_schema import WorkDaySchema
from dashboard.services.base import BaseService
from dashboard.services.technic_sheet import TechnicSheetService
from logger import getLogger

log = getLogger(__name__)


class EditApplicationTechnic:
    pass


class ApplicationTechnicService(BaseService):
    model = ApplicationTechnic
    schema = ApplicationTechnicSchema
    CACHE_TTL = 10

    class CacheKeys(enum.Enum):
        APP_TECH_FOR_DATE = "app_tech_for_date"

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
            at = cls.model.objects.create(**app_technic_data.model_dump())
            return at
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
                # at.technic_sheet.decrement_count_application()
                TechnicSheetService.decrement_count_application(at.technic_sheet)
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
    def reject_or_accept(
            cls,
            app_technic_id: int,
            workday_data: WorkDaySchema
    ) -> Literal["accept", "reject"] | None:
        """
        Отвергнуть заявку
        :param workday_data:
        :param app_technic_id:
        :return: reject | accept
        """
        at = cls.get_object(id=app_technic_id)
        status = None
        if at:
            if at.is_cancelled:
                at.isChecked = False
                at.is_cancelled = False
                TechnicSheetService.increment_count_application(at.technic_sheet)
                at.save()
                status = "accept"
            else:
                at.isChecked = False
                at.is_cancelled = True
                TechnicSheetService.decrement_count_application(at.technic_sheet)
                at.save()
                status = "reject"
            cache.delete(f"{cls.CacheKeys.APP_TECH_FOR_DATE.value}:{workday_data.date}")
        return status

    @classmethod
    def get_app_tech_for_date(cls, workday_data: WorkDaySchema) -> list[ApplicationTechnicSchema]:
        cache_key = f"{cls.CacheKeys.APP_TECH_FOR_DATE.value}:{workday_data.date}"
        cache_ttl = 60 * 60

        app_tech_for_cache = cache.get(cache_key)
        if app_tech_for_cache is None:
            app_tech = cls.get_queryset(application_today__date_id=workday_data.id, isArchive=False)
            app_tech_data = [cls.schema(**at.to_dict()) for at in app_tech]
            if cls.USE_CACHE:
                cache.set(cache_key, app_tech_for_cache, cache_ttl)
            return app_tech_data
        else:
            cache.touch(cache_key, cache_ttl)
            return app_tech_for_cache

    @classmethod
    def filter_app_tech_by_at_id_from_data(
        cls, app_today_id: int, data: list[ApplicationTechnicSchema]
    ) -> list[ApplicationTechnicSchema]:
        app_tech = [at for at in data if at.application_today == app_today_id]
        return app_tech
