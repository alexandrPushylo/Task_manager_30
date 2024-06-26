from datetime import date, timedelta

from dashboard.models import DriverSheet, WorkDaySheet, User
import dashboard.assets as ASSETS
import dashboard.utilities as U

from logger import getLogger

log = getLogger(__name__)


def change_status(driver_sheet_id):
    try:
        driver_sheet = DriverSheet.objects.get(id=driver_sheet_id)
        if driver_sheet.status:
            driver_sheet.status = False
            log.info(f"driver_sheet с id {driver_sheet_id} установлен статус False")
        else:
            driver_sheet.status = True
            log.info(f"driver_sheet с id {driver_sheet_id} установлен статус True")
        driver_sheet.save(update_fields=['status'])
    except DriverSheet.DoesNotExist:
        log.error(f"Driver_sheet с id {driver_sheet_id} не существует")


def create_driver_sheets(workday: WorkDaySheet):
    """
    Подготовка driver_sheets (prepare_driver_sheet)
    Копирование или создание записей, удаление дубликатов.
    :param workday: WorkDaySheet
    :return:
    """
    driver_sheets = DriverSheet.objects.filter(date=workday, isArchive=False)
    count_driver_sheets = driver_sheets.count()

    drivers_list = User.objects.filter(isArchive=False, post=ASSETS.DRIVER)
    count_driver = drivers_list.count()

    if count_driver != count_driver_sheets:
        log.info(f"DriverSheet на {workday.date} не готов")

        last_workday = WorkDaySheet.objects.filter(date__lt=workday.date, status=True).first()
        last_driver_sheet = DriverSheet.objects.filter(date=last_workday, isArchive=False)

        if count_driver > count_driver_sheets:
            log.info(f"count_driver > count_driver_sheets {count_driver} > {count_driver_sheets}")

            if last_driver_sheet.exists():  # COPY
                log.info(f"last_driver_sheet.exists() is {last_driver_sheet.exists()} - Копирование")

                current_driver_sheet = [DriverSheet(
                    date=workday,
                    driver=ds.driver,
                    status=ds.status) for ds in last_driver_sheet]

            else:  # CREATE
                log.info(f"last_driver_sheet.exists() is {last_driver_sheet.exists()} - Создание")

                current_driver_sheet = [DriverSheet(
                    date=workday,
                    driver=driver) for driver in drivers_list]

            DriverSheet.objects.bulk_create(current_driver_sheet)

        if count_driver_sheets != 0 and count_driver != count_driver_sheets:  # Delete duplicate
            log.info(f"count_driver < count_driver_sheets {count_driver} < {count_driver_sheets}")
            log.info(f"Поиск дубликата")
            for driver in drivers_list:
                double_ds = DriverSheet.objects.filter(date=workday, driver=driver)
                if double_ds.count() > 1:
                    log.info(f"Дубликат {double_ds.first()} удален")
                    double_ds.first().delete()

        if count_driver == count_driver_sheets:
            log.info(f"count_driver = count_driver_sheets {count_driver} = {count_driver_sheets}")

    else:
        log.info(f"DriverSheet на {workday.date} существует")
