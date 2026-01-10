import enum
import random

from django.core.cache import cache

from dashboard.models import TechnicSheet
from django.db.models import F, QuerySet  # type: ignore
from dashboard.schemas.technic_sheet_schema import (
    TechnicSheetSchema,
    WorkloadTechnicSheetSchema,
)
from dashboard.schemas.work_day_sheet_schema import WorkDaySchema
from dashboard.services.base import BaseService
from logger import getLogger


log = getLogger(__name__)


class TechnicSheetService(BaseService):
    model = TechnicSheet
    schema = TechnicSheetSchema
    CACHE_TTL = 10
    class CacheKeys(enum.Enum):
        WORKLOAD_LIST = 'workload_list'
        TECH_SHEET_FOR_DAY = "tech_sheet_for_day"

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
    def change_status(cls, technic_sheet_id: int) -> bool | None:
        ts = cls.get_object(id=technic_sheet_id)
        if ts:
            if ts.status:
                ts.status = False
                log.info(f"technic_sheet id {technic_sheet_id} the status is set to False")
                ts.save(update_fields=["status"])
                status = False
            else:
                ts.status = True
                log.info("technic_sheet id {technic_sheet_id} the status is set to True")
                ts.save(update_fields=["status"])
                status = True
            cache.delete(f"{cls.CacheKeys.WORKLOAD_LIST.value}:{ts.date.id}")
            cache.delete(f"{cls.CacheKeys.TECH_SHEET_FOR_DAY.value}:{ts.date.date}")
            return status
        return None

    @classmethod
    def get_workload_list_of_technic_sheet(cls, workday_sheet_id: int) -> list[WorkloadTechnicSheetSchema]:
        """
        Получить list загруженности technic_sheet за workday
        :param workday_sheet_id:
        :return: {'id',
            'technic__title',
            'driver_sheet_id',
            'count_application'}
        """
        cache_key = f"{cls.CacheKeys.WORKLOAD_LIST.value}:{workday_sheet_id}"
        cache_ttl = 60
        workload_list_from_cache = cache.get(cache_key)
        if workload_list_from_cache is None:
            workload_list = (
                cls.get_queryset(
                    isArchive=False,
                    status=True,
                    date_id=workday_sheet_id,
                    driver_sheet__isnull=False,
                    driver_sheet__status=True,
                )
                .select_related("driver_sheet", "technic")
                .values("id", "technic__title", "driver_sheet_id", "count_application")
            )
            workload_list_data = [WorkloadTechnicSheetSchema(**wl) for wl in workload_list]
            if cls.USE_CACHE:
                cache.set(cache_key, workload_list_data, cache_ttl)
            return workload_list_data
        else:
            return workload_list_from_cache

    @classmethod
    def get_freelist_of_technic_sheet(cls,
                                      technic_title: str,
                                      workload_list: list[WorkloadTechnicSheetSchema],
                                      get_only_free: bool = True
                                      ) -> list[WorkloadTechnicSheetSchema]:
        """
        Получить список незанятых (get_only_free=True)
        или любых (get_only_free=False) данных technic_sheet для technic_title
        :param workload_list:
        :param technic_title: Название техники
        :param get_only_free: True получить незанятых; False получить менее занятых
        :return: [{'id',
            'technic__title',
            'driver_sheet_id',
            'count_application'},...]
        """
        if workload_list:
            if get_only_free:
                free_list = [item for item in workload_list
                             if item.technic__title == technic_title and item.count_application == 0]
            else:
                free_list = [item for item in workload_list if item.technic__title == technic_title]
            return free_list
        return []

    @classmethod
    def get_least_busy_technic_sheet(
            cls,
            freelist_of_technic_sheet: list[WorkloadTechnicSheetSchema]
            ) -> WorkloadTechnicSheetSchema | None:
        """
        Получить наименее занятого dict(technic_sheet)
        :param freelist_of_technic_sheet:
        :return: {'id',
            'technic__title',
            'driver_sheet_id',
            'count_application'}
        """
        if freelist_of_technic_sheet:
            least_busy_technic_sheet = sorted(
                freelist_of_technic_sheet, key=lambda item: item.count_application
            )[0]
            return least_busy_technic_sheet
        log.warning("get_least_busy_technic_sheet(): free_technic_sheet_list is empty")
        return None

    @classmethod
    def get_some_technic_sheet(
            cls,
            technic_title: str,
            workday_sheet_id: int
    ):
        workload_list = cls.get_workload_list_of_technic_sheet(workday_sheet_id)
        freelist_of_technic_sheet = cls.get_freelist_of_technic_sheet(
            technic_title=technic_title,
            workload_list=workload_list
        )
        if freelist_of_technic_sheet:
            random_freelist_of_technic_sheet: WorkloadTechnicSheetSchema = random.choice(freelist_of_technic_sheet)
            return cls.get_object(id=random_freelist_of_technic_sheet.id)
        else:
            any_technic_sheet_list = cls.get_freelist_of_technic_sheet(
                technic_title=technic_title,
                workload_list=workload_list,
                get_only_free=False
            )
            least_busy_technic_sheet = cls.get_least_busy_technic_sheet(any_technic_sheet_list)
            if least_busy_technic_sheet:
                return cls.get_object(id=least_busy_technic_sheet.id)
            else:
                return None

    @classmethod
    def get_tech_sheet_for_date(cls, workday_data: WorkDaySchema) -> list[TechnicSheetSchema]:
        cache_key = f"{cls.CacheKeys.TECH_SHEET_FOR_DAY.value}:{workday_data.date}"
        cache_ttl = 60 * 60
        tech_sheet_from_cache = cache.get(cache_key)
        if tech_sheet_from_cache is None:
            tech_sheet = cls.get_queryset(date_id=workday_data.id)
            tech_sheet_data = [cls.schema(**ts.to_dict()) for ts in tech_sheet]
            if cls.USE_CACHE:
                cache.set(cache_key, tech_sheet_data, cache_ttl)
            return tech_sheet_data
        else:
            cache.touch(cache_key, cache_ttl)
            return tech_sheet_from_cache

    @classmethod
    def increment_count_application(cls, technic_sheet_inst: TechnicSheet):
        technic_sheet_inst.increment_count_application()
        cache.delete(f"{cls.CacheKeys.WORKLOAD_LIST.value}:{technic_sheet_inst.date.id}")
        cache.delete(f"{cls.CacheKeys.TECH_SHEET_FOR_DAY.value}:{technic_sheet_inst.date.date}")


    @classmethod
    def decrement_count_application(cls, technic_sheet_inst: TechnicSheet):
        technic_sheet_inst.decrement_count_application()
        cache.delete(f"{cls.CacheKeys.WORKLOAD_LIST.value}:{technic_sheet_inst.date.id}")
        cache.delete(f"{cls.CacheKeys.TECH_SHEET_FOR_DAY.value}:{technic_sheet_inst.date.date}")

    @classmethod
    def filter_tech_sheet_by_id(
            cls,
            tech_sheet_id: int,
            tech_sheet_list: list[TechnicSheetSchema]
    ) -> TechnicSheetSchema | None:
        for tech_sheet in tech_sheet_list:
            if tech_sheet.id == tech_sheet_id:
                return tech_sheet
        return None
