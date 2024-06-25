from datetime import date, timedelta

from dashboard.models import WorkDaySheet
import dashboard.assets as ASSETS
import dashboard.utilities as U

from logger import getLogger
log = getLogger(__name__)


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


def get_workday(_date: date) -> WorkDaySheet:
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
