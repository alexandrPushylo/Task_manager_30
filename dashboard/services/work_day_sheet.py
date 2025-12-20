from datetime import date, timedelta
from django.core.exceptions import ValidationError
from django.db.models import QuerySet  # type: ignore
from django.core.cache import cache

from dashboard.models import WorkDaySheet
import dashboard.utilities as U
import dashboard.assets as A
from dashboard.schemas.work_day_sheet_schema import (
    WorkDaySchema,
    WorkDaysWithWeekdaySchema,
)
from config.settings import USE_CACHE

from logger import getLogger

log = getLogger(__name__)
TODAY = date.today()


def get_workday_sheet(*args, **kwargs) -> WorkDaySchema | None:
    cache_key = U.validate_cache_name(f'get_workday_sheet:{args},{kwargs}')
    cache_timeout = 10
    try:
        cache_workday_sheet: WorkDaySchema | None = cache.get(cache_key)
        if USE_CACHE and cache_workday_sheet is None:
            workday_sheet = WorkDaySheet.objects.get(*args, **kwargs)
            workday_sheet_scheme: WorkDaySchema = WorkDaySchema(**workday_sheet.to_dict())
            cache.set(cache_key, workday_sheet_scheme, timeout=cache_timeout)
            return workday_sheet_scheme
        return cache_workday_sheet
    except WorkDaySheet.DoesNotExist:
        log.warning(f"Workday with: {args} & {kwargs} does not exist")
        return None


def get_workday(_date: date) -> WorkDaySchema:
    """
    :param _date:
    :return:
    """
    try:
        # workday = WorkDaySheet.objects.get(date=_date)
        workday = get_workday_sheet(date=_date)
        return workday
    except WorkDaySheet.DoesNotExist:
        log.warning(f"Workday: {_date} does not exist")
        status = prepare_workday(_date)
        return get_workday(_date) if status else get_workday(TODAY)
    except ValidationError:
        log.error("The value has an incorrect date format.")
        return get_workday(TODAY)


def get_workday_queryset(*args, **kwargs) -> list[WorkDaySchema | None]:
    """
    :param kwargs:
    :return:
    """
    cache_key = U.validate_cache_name(f"get_workday_queryset:{args},{kwargs}")
    cache_timeout = 10

    cache_workday_sheet: list[WorkDaySchema | None] = cache.get(cache_key)
    if USE_CACHE and cache_workday_sheet is None:
        workday_queryset = WorkDaySheet.objects.filter(*args, **kwargs)
        workday_queryset_scheme = [WorkDaySchema(**wd.to_dict()) for wd in workday_queryset]
        cache.set(cache_key, workday_queryset_scheme, timeout=cache_timeout)
        return workday_queryset_scheme

    return cache_workday_sheet

# def get_workday_queryset(select_related: tuple = (),
#                          order_by: tuple = (),
#                          **kwargs) -> QuerySet[WorkDaySheet]:
#     """
#     :param select_related:
#     :param order_by:
#     :param kwargs:
#     :return:
#     """
#     workday = WorkDaySheet.objects.filter(**kwargs)
#     if select_related:
#         workday = workday.select_related(*select_related)
#     if order_by:
#         workday = workday.order_by(*order_by)
#     return workday


def prepare_workday(_date: date) -> bool:
    if WorkDaySheet.objects.filter(date__gte=_date).count() < 14:
        for n in range(21):
            day = date.today() + timedelta(days=n)
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


def get_range_workdays(start_date: date, before_days: int, after_days: int) -> list[WorkDaySchema]:
    """
    Получить диапазон объектов WorkDaySheet от before_days до after_days
    :param start_date: дата отсчета
    :param before_days: количество дней до даты отсчета
    :param after_days: количество дней после даты отсчета
    :return: диапазон объектов WorkDaySheet.objects
    """

    # workdays = WorkDaySheet.objects.filter(
    workdays = get_workday_queryset(
        date__gte=start_date - timedelta(days=before_days),
        date__lte=start_date + timedelta(days=after_days)
    )
    if before_days+after_days+1 != len(workdays):
        prepare_workday(start_date)
    return workdays

def get_range_workdays_with_weekdays(
        start_date: date,
        before_days: int,
        after_days: int,
        short_weekdays: bool = False,
) -> list[WorkDaysWithWeekdaySchema]:
    workdays = get_range_workdays(start_date, before_days, after_days)

    out_list = [
        WorkDaysWithWeekdaySchema(
            **workday.model_dump(),
            weekday=A.WEEKDAY[workday.date.weekday()][:3] if short_weekdays else A.WEEKDAY[workday.date.weekday()]
        )
        for workday in workdays]
    return out_list


def get_next_workday(current_day: date = TODAY) -> WorkDaySchema:
    """
    Получить следующий рабочий день
    :param current_day: дата отсчета по умолчанию TODAY
    :return: объект WorkDaySchema
    """
    next_workday = get_workday_queryset(status=True, date__gt=current_day)[::-1][0]
    return next_workday


def get_prev_workday(current_day: date = TODAY) -> WorkDaySchema:
    """
    Получить предыдущий рабочий день
    :param current_day: дата отсчета по умолчанию TODAY
    :return: объект WorkDaySchema
    """
    next_workday = get_workday_queryset(status=True, date__lt=current_day)[0]
    return next_workday


def get_current_day(request) -> WorkDaySchema:
    """
    :param request: request.GET.get('current_day')
    :return: WorkDaySchema
    """
    current_day = request.GET.get('current_day')
    if current_day is None or current_day == '':
        return get_workday(U.TODAY)
    else:
        return get_workday(current_day)


def change_status(*args, **kwargs) -> bool:
    try:
        cache_key = U.validate_cache_name(f'get_workday_sheet:{args},{kwargs}')
        workday = WorkDaySheet.objects.get(*args, **kwargs)
        # workday = get_workday_sheet(id=work_day_id)
        if workday.status:
            workday.status = False
            log.info(f"work_day {workday.date} is set as a day off")
        else:
            workday.status = True
            log.info(f"work_day {workday.date} is set as a working day")
        workday.save(update_fields=['status'])
        cache.delete(cache_key)
        return True
    except WorkDaySheet.DoesNotExist:
        log.error(f"A workday with id does not exist")
        return False
    except ValueError:
        log.error('change_status(): ValueError')
        return False
