import enum
from datetime import date, timedelta
from django.db.models import QuerySet  # type: ignore
from django.core.cache import cache

from dashboard.models import WorkDaySheet
import dashboard.assets as A
from dashboard.schemas.work_day_sheet_schema import (
    WorkDaySchema,
    WorkDaysWithWeekdaySchema,
)
from dashboard.services.base import BaseService

from logger import getLogger

log = getLogger(__name__)
TODAY = date.today()


class WorkDayService(BaseService):
    model = WorkDaySheet
    schema = WorkDaySchema
    CACHE_TTL = 10

    class CacheKeys(enum.Enum):
        RANGE_WORKDAYS = "get_range_of_workdays"
        CURRENT_DATE_DATA = "current_date_data"

    @classmethod
    def get_object(cls, *args, **kwargs) -> WorkDaySheet | None:
        try:
            obj = cls.model.objects.get(*args, **kwargs)
            return obj
        except cls.model.DoesNotExist:
            log.warning(f"Workday with: {args} & {kwargs} does not exist")
            return None
        except cls.model.MultipleObjectsReturned:
            log.warning(f"Workday with: {args} & {kwargs} already exists")
            return None

    @classmethod
    def get_queryset(cls, *args, **kwargs) -> QuerySet[WorkDaySheet]:
        try:
            queryset = cls.model.objects.filter(*args, **kwargs)
            return queryset
        except ValueError:
            log.warning(f"get_users_queryset({kwargs}): ValueError")
            return cls.model.objects.none()

    @classmethod
    def prepare_workday_sheet(cls, date_: date) -> bool:
        if WorkDaySheet.objects.filter(date__gte=date_).count() < 14:
            for i in range(21):
                day = date.today() + timedelta(days=i)
                if day.weekday() in (5, 6):
                    status = False
                else:
                    status = True
                WorkDaySheet.objects.update_or_create(date=day, defaults={'status': status})
            log.info("Prepare workday completed")
            return True
        else:
            log.info("Prepare workday not completed")
            return False

    @classmethod
    def _get_workdays_range(cls) -> list[WorkDaySchema]:
        cache_key = f"{cls.CacheKeys.RANGE_WORKDAYS.value}"
        cache_ttl = 60 * 60

        range_of_workdays_from_cache = cache.get(cache_key) if cls.USE_CACHE else None
        if range_of_workdays_from_cache is None:
            workdays_queryset = cls.model.objects.filter(
                date__gte=cls.TODAY - timedelta(days=7),
                date__lte=cls.TODAY + timedelta(days=21)
            )
            workdays_data = [WorkDaySchema(**wd.to_dict()) for wd in workdays_queryset]
            if cls.USE_CACHE:
                cache.set(cache_key, workdays_data, cache_ttl)
            return workdays_data
        else:
            cache.touch(cache_key, cache_ttl)
            return range_of_workdays_from_cache

    @classmethod
    def get_range_of_workdays(
            cls,
            start_date: date,
            before_days: int,
            after_days: int,
            revers: bool = False
    ) -> list[WorkDaySchema]:
        """
        Получить диапазон объектов WorkDaySheet от before_days до after_days
        :param revers:
        :param start_date: дата отсчета
        :param before_days: количество дней до даты отсчета
        :param after_days: количество дней после даты отсчета
        :return: диапазон объектов WorkDaySheet.objects
        """
        workday_range = cls._get_workdays_range()
        before = start_date - timedelta(days=before_days)
        after = start_date + timedelta(days=after_days)
        days_range = [
            day
            for day in workday_range
            if before <= day.date <= after
        ]
        if revers:
            days_range = days_range[::-1]
        return days_range

    @classmethod
    def get_range_of_workdays_with_weekdays(
            cls,
            start_date: date,
            before_days: int,
            after_days: int,
            short_weekdays: bool = False,
            revers: bool = False
    ) -> list[WorkDaysWithWeekdaySchema]:
        range_of_workdays = cls.get_range_of_workdays(start_date, before_days, after_days, revers)
        workdays_with_weekdays = [
            WorkDaysWithWeekdaySchema(
                **workday.model_dump(),
                weekday=(
                    A.WEEKDAY[workday.date.weekday()][:3]
                    if short_weekdays
                    else A.WEEKDAY[workday.date.weekday()]
                ),
            )
            for workday in range_of_workdays
        ]
        return workdays_with_weekdays

    @classmethod
    def get_next_workday(cls, current_date: date = TODAY) -> WorkDaySchema:
        """
        Получить следующий рабочий день
        :param current_date: дата отсчета по умолчанию TODAY
        :return: объект WorkDaySchema
        """
        next_day = cls.get_queryset(status=True, date__gt=current_date).last()
        if not next_day:
            cls.prepare_workday_sheet(current_date)
            next_day = cls.get_queryset(status=True, date__gt=current_date).last()
        next_day_data = WorkDaySchema(**next_day.to_dict())
        return next_day_data

    @classmethod
    def get_prev_workday(cls, current_date: date = TODAY) -> WorkDaySchema:
        """
        Получить предыдущий рабочий день
        :param current_date: дата отсчета по умолчанию TODAY
        :return: объект WorkDaySchema
        """
        prev_day = cls.get_queryset(status=True, date__lt=current_date).first()
        prev_day_data = WorkDaySchema(**prev_day.to_dict())
        return prev_day_data

    @classmethod
    def change_status(cls, *args, **kwargs) -> bool:
        wday = cls.get_object(*args, **kwargs)
        if wday:
            status = wday.status
            if status:
                wday.status = False
                log.info(f"work_day {wday.date} is set as a day off")
            else:
                wday.status = True
                log.info(f"work_day {wday.date} is set as a working day")
            wday.save(update_fields=["status"])
            cache.delete(cls.CacheKeys.RANGE_WORKDAYS.value)
            cache.delete(f"{cls.CacheKeys.CURRENT_DATE_DATA.value}:{wday.date}")
            return True
        else:
            return False

    @classmethod
    def get_current_date_data(cls, current_date) -> WorkDaySchema | None:
        cache_kay = f"{cls.CacheKeys.CURRENT_DATE_DATA.value}:{current_date}"
        cache_ttl = 60 * 60
        current_date_data_from_cache = cache.get(cache_kay) if cls.USE_CACHE else None
        if current_date_data_from_cache is None:
            current_date_data = cls.get_object(date = current_date)
            current_date_data__data = WorkDaySchema(**current_date_data.to_dict())
            if cls.USE_CACHE:
                cache.set(cache_kay, current_date_data__data, cache_ttl)
            return current_date_data__data
        else:
            cache.touch(cache_kay, cache_ttl)
            return current_date_data_from_cache
