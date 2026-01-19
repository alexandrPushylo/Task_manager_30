import enum
from typing import Literal

from django.core.cache import cache
from django.db.models import QuerySet  # type: ignore

import dashboard.assets as ASSETS
from dashboard.models import ApplicationToday
from dashboard.schemas.application_today_schema import (
    ApplicationTodaySchema,
    CreateApplicationTodaySchema,
)
from dashboard.schemas.work_day_sheet_schema import WorkDaySchema
from dashboard.services.base import BaseService
from logger import getLogger

log = getLogger(__name__)


class ApplicationTodayService(BaseService):
    model = ApplicationToday
    schema = ApplicationTodaySchema
    CACHE_TTL = 10

    class CacheKeys(enum.Enum):
        APPLICATIONS_TODAY_FOR_DATE = "applications_today_for_date"

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
                    at =  cls.model.objects.create(
                        construction_site_id=data.construction_site_id,
                        date_id=data.date_id
                    )
            cache.delete(f"{cls.CacheKeys.APPLICATIONS_TODAY_FOR_DATE.value}:{at.date.date}")
            return at
        except ValueError:
            log.error(f"get_or_create_app_today(): ValueError")
            return None

    @classmethod
    def get_or_create(cls, *args, **kwargs) -> tuple[ApplicationToday, bool]:
        (obj, created) = cls.model.objects.get_or_create(*args, **kwargs)
        if created:
            cache.delete(
                f"{cls.CacheKeys.APPLICATIONS_TODAY_FOR_DATE.value}:{obj.date.date}"
            )
        return obj, created

    @classmethod
    def delete(cls, **kwargs) -> ApplicationToday | None:
        at = cls.get_object(**kwargs)
        if at:
            at.isArchive = True
            at.status = ASSETS.ApplicationTodayStatus.DELETED.title
            at.save(update_fields=['status', 'isArchive'])
            cache.delete(f"{cls.CacheKeys.APPLICATIONS_TODAY_FOR_DATE.value}:{at.date.date}")
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
            cache.delete(
                f"{cls.CacheKeys.APPLICATIONS_TODAY_FOR_DATE.value}:{at.date.date}"
            )
            return at
        return None

    @classmethod
    def get_app_today_for_date(cls, workday_data: WorkDaySchema) -> list[ApplicationTodaySchema]:
        cache_key = f"{cls.CacheKeys.APPLICATIONS_TODAY_FOR_DATE.value}:{workday_data.date}"
        cache_ttl = 60 * 60

        app_today_from_cache = cache.get(cache_key) if cls.USE_CACHE else None
        if app_today_from_cache is None:
            app_today = cls.get_queryset(date_id = workday_data.id)
            app_today_data = [cls.schema(**at.to_dict()) for at in app_today]
            if cls.USE_CACHE:
                cache.set(cache_key, app_today_data, cache_ttl)
            return app_today_data
        else:
            cache.touch(cache_key, cache_ttl)
            return app_today_from_cache

    @classmethod
    def make_edited(cls, app_today_instance: ApplicationToday, status: str = None):
        app_today_instance.make_edited(status)
        cache.delete(
            f"{cls.CacheKeys.APPLICATIONS_TODAY_FOR_DATE.value}:{app_today_instance.date.date}"
        )

    @classmethod
    def set_next_status(cls, app_today_instance: ApplicationToday, clear_cache: bool = True):
        app_today_instance.set_next_status()
        if clear_cache:
            cache.delete(
                f"{cls.CacheKeys.APPLICATIONS_TODAY_FOR_DATE.value}:{app_today_instance.date.date}"
            )

    @classmethod
    def get_app_today_by_cs_id_from_data(
            cls,
            constr_site_id: int,
            data: list[ApplicationTodaySchema]
    ) -> ApplicationTodaySchema | None:
        for at in data:
            if at.construction_site == constr_site_id:
                return at
        return None
