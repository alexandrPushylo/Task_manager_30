import enum

from django.core.cache import cache
from django.db import models
from django.db.models import QuerySet
from dashboard.models import DriverSheet

from dashboard.schemas.driver_sheet_schema import DriverSheetSchema
from dashboard.schemas.work_day_sheet_schema import WorkDaySchema
from dashboard.services.base import BaseService
from dashboard.services.technic_sheet import TechnicSheetService

from logger import getLogger

log = getLogger(__name__)


class DriverSheetService(BaseService):
    model = DriverSheet
    schema = DriverSheetSchema
    CACHE_TTL = 10

    class CacheKeys(enum.Enum):
        DRIVER_SHEET_FOR_DAY = 'driver_sheet_for_day'

    @classmethod
    def get_object(cls, *args, **kwargs) -> model | None:
        try:
            obj = cls.model.objects.get(*args, **kwargs)
            return obj
        except cls.model.DoesNotExist:
            log.warning(f"{cls} with: {args} & {kwargs} does not exist")
            return None
        except cls.model.MultipleObjectsReturned:
            log.warning(f"{cls} with: {args} & {kwargs} already exists")
            return None
        except ValueError:
            log.error(f"{cls} ({kwargs}): ValueError")
            return None

    @classmethod
    def get_queryset(cls, *args, **kwargs) -> QuerySet[model]:
        try:
            queryset = cls.model.objects.filter(*args, **kwargs)
            return queryset
        except ValueError:
            log.warning(f"{cls} ({kwargs}): ValueError")
            return cls.model.objects.none()

    @classmethod
    def change_status(cls, driver_sheet_id: int) -> bool | None:
        """
        Изменение статуса DriverSheet
        :param driver_sheet_id:
        :return:
        """
        driver_sheet: models.Model | DriverSheet | None  = cls.get_object(id=driver_sheet_id)
        if driver_sheet:
            if driver_sheet.status:
                driver_sheet.status = False
                log.info(f"driver_sheet with id {driver_sheet_id} status set to False")
                driver_sheet.save(update_fields=["status"])
                status = False
            else:
                driver_sheet.status = True
                log.info(
                    f"the driver_sheet with id {driver_sheet_id} has the status set to True"
                )
                driver_sheet.save(update_fields=["status"])
                status = True
            cache.delete(f"{cls.CacheKeys.DRIVER_SHEET_FOR_DAY.value}:{driver_sheet.date.date}")
            cache.delete(f"{TechnicSheetService.CacheKeys.WORKLOAD_LIST.value}:{driver_sheet.date.id}")
            return status
        return None

    @classmethod
    def get_driver_sheet_for_date(cls, workday_data: WorkDaySchema) -> list[DriverSheetSchema]:
        cache_key = f"{cls.CacheKeys.DRIVER_SHEET_FOR_DAY.value}:{workday_data.date}"
        cache_ttl = 60 * 60

        driver_sheet_from_cache = cache.get(cache_key) if cls.USE_CACHE else None
        if driver_sheet_from_cache is None:
            driver_sheet = cls.get_queryset(date_id=workday_data.id)
            driver_sheet_data = [cls.schema(**ds.to_dict()) for ds in driver_sheet]
            if cls.USE_CACHE:
                cache.set(cache_key, driver_sheet_data, cache_ttl)
            return driver_sheet_data
        else:
            cache.touch(cache_key, cache_ttl)
            return driver_sheet_from_cache

    @classmethod
    def filter_driver_sheet_by_id(
        cls, driver_sheet_id: int, driver_sheet_list: list[DriverSheetSchema]
    ) -> DriverSheetSchema | None:
        for driver_sheet in driver_sheet_list:
            if driver_sheet.id == driver_sheet_id:
                return driver_sheet
        return None
