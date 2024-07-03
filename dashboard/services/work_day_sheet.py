from datetime import date, timedelta, datetime

from dashboard.models import WorkDaySheet
import dashboard.assets as ASSETS
import dashboard.utilities as U

from logger import getLogger

log = getLogger(__name__)
TODAY = date.today()
NOW = datetime.now().time()


def prepare_workday(_date: date) -> WorkDaySheet | None:
    if WorkDaySheet.objects.filter(date__gte=_date).count() < 14:
        for n in range(21):
            day = date.today() + timedelta(days=n)
            if day.weekday() in (5, 6):
                status = False
            else:
                status = True
            WorkDaySheet.objects.update_or_create(date=day, defaults={'status': status})
        log.info(f"Prepare workday выполнен")
    else:
        log.info(f"Prepare workday не выполнен")
        return None


def get_range_workdays(start_date: date, before_days: int, after_days: int) -> WorkDaySheet.objects:
    """
    Получить диапазон объектов WorkDaySheet от before_days до after_days
    :param start_date: дата отсчета
    :param before_days: количество дней до даты отсчета
    :param after_days: количество дней после даты отсчета
    :return: диапазон объектов WorkDaySheet.objects
    """
    workdays = WorkDaySheet.objects.filter(
        date__gte=start_date - timedelta(days=before_days),
        date__lte=start_date + timedelta(days=after_days)
    )
    return workdays


def get_next_workday(current_day: date = TODAY) -> WorkDaySheet:
    """
    Получить следующий рабочий день
    :param current_day: дата отсчета по умолчанию TODAY
    :return: объект WorkDaySheet
    """
    next_workday = WorkDaySheet.objects.filter(status=True, date__gt=current_day).last()
    return next_workday


def get_prev_workday(current_day: date = TODAY) -> WorkDaySheet:
    """
    Получить предыдущий рабочий день
    :param current_day: дата отсчета по умолчанию TODAY
    :return: объект WorkDaySheet
    """
    next_workday = WorkDaySheet.objects.filter(status=True, date__lt=current_day).first()
    return next_workday


def get_current_day(request) -> WorkDaySheet:
    """

    :param request: request.GET.get('current_day')
    :return: WorkDaySheet
    """
    current_day = request.GET.get('current_day')
    if current_day is None or current_day == '':
        return get_workday(U.TODAY)
    else:
        return get_workday(current_day)


def get_workday(_date: date) -> WorkDaySheet:
    """
    :param _date:
    :return:
    """
    try:
        workday = WorkDaySheet.objects.get(date=_date)
        return workday
    except WorkDaySheet.DoesNotExist:
        log.error(f"Workday: {_date} не существует")
        prepare_workday(_date)
        work_day = get_workday(_date)
        return work_day


def change_status(work_day_id):
    try:
        workday = WorkDaySheet.objects.get(id=work_day_id)
        if workday.status:
            workday.status = False
            log.info(f"work_day {workday.date} установлен как выходной")
        else:
            workday.status = True
            log.info(f"work_day {workday.date} установлен как рабочий")
        workday.save(update_fields=['status'])
    except WorkDaySheet.DoesNotExist:
        log.error(f"Workday с id {work_day_id} не существует")
    except ValueError:
        log.error('change_status(): ValueError')