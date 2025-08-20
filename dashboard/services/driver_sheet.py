from django.db.models import QuerySet  # type: ignore
from dashboard.models import DriverSheet, WorkDaySheet, User
import dashboard.assets as ASSETS

from logger import getLogger

log = getLogger(__name__)


def get_driver_sheet_queryset(select_related: tuple = (),
                              order_by: tuple = (),
                              **kwargs) -> QuerySet[DriverSheet]:
    """
    :param select_related:
    :param order_by:
    :param kwargs:
    :return:
    """

    driver_sheet = DriverSheet.objects.filter(**kwargs)
    if select_related:
        driver_sheet = driver_sheet.select_related(*select_related)
    if order_by:
        driver_sheet = driver_sheet.order_by(*order_by)
    return driver_sheet


def get_driver_sheet(**kwargs) -> DriverSheet:
    """
    :param kwargs:
    :return:
    """
    try:
        driver_sheet = DriverSheet.objects.get(**kwargs)
        return driver_sheet
    except DriverSheet.DoesNotExist:
        log.warning(f'get_driver_sheet({kwargs}): DriverSheet.DoesNotExist')
        return DriverSheet.objects.none()
    except DriverSheet.MultipleObjectsReturned:
        log.error(f'get_driver_sheet({kwargs}): DriverSheet.MultipleObjectsReturned')
        return DriverSheet.objects.none()
    except ValueError:
        log.error(f"get_driver_sheet{kwargs}() - ValueError ")
        return DriverSheet.objects.none()


def change_status(driver_sheet_id) -> bool | None:
    """
    Изменение статуса DriverSheet
    :param driver_sheet_id:
    :return:
    """
    try:
        driver_sheet = DriverSheet.objects.get(id=driver_sheet_id)
        if driver_sheet.status:
            driver_sheet.status = False
            log.info(f"driver_sheet with id {driver_sheet_id} status set to False")
            driver_sheet.save(update_fields=['status'])
            return False
        else:
            driver_sheet.status = True
            log.info(f"the driver_sheet with id {driver_sheet_id} has the status set to True")
            driver_sheet.save(update_fields=['status'])
            return True
    except DriverSheet.DoesNotExist:
        log.warning(f"Driver_sheet with id {driver_sheet_id} does not exist")
        return None
    except ValueError:
        log.error(f"Driver_sheet change_status() - ValueError")
        return None


def prepare_driver_sheet(workday: WorkDaySheet):
    """
    Подготовка driver_sheets (prepare_driver_sheet)
    Копирование или создание записей, удаление дубликатов.
    :param workday: WorkDaySheet
    :return:
    """
    driver_sheets = DriverSheet.objects.filter(date=workday, isArchive=False)
    count_driver_sheets = driver_sheets.count()

    drivers_list = User.objects.filter(isArchive=False, post=ASSETS.UserPosts.DRIVER.title)
    count_driver = drivers_list.count()

    if count_driver != count_driver_sheets:
        log.info("DriverSheet is not ready")

        last_workday = WorkDaySheet.objects.filter(date__lt=workday.date, status=True).first()
        last_driver_sheet = DriverSheet.objects.filter(date=last_workday, isArchive=False)

        if count_driver > count_driver_sheets:
            log.info("count_driver > count_driver_sheets %s > %s" % (count_driver, count_driver_sheets))

            if last_driver_sheet.count() == count_driver:  # COPY
                log.info("last_driver_sheet.exists() is %s - COPY" % last_driver_sheet.exists())

                current_driver_sheet = [DriverSheet(
                    date=workday,
                    driver=ds.driver,
                    status=ds.status) for ds in last_driver_sheet]

            else:  # CREATE
                log.info("last_driver_sheet.exists() is %s - CREATE" % last_driver_sheet.exists())

                exclude_drivers = driver_sheets.values_list('driver_id', flat=True)

                current_driver_sheet = [DriverSheet(
                    date=workday,
                    driver=driver) for driver in drivers_list if driver.id not in exclude_drivers]

            DriverSheet.objects.bulk_create(current_driver_sheet)

        if count_driver_sheets != 0 and count_driver != count_driver_sheets:  # Delete duplicate
            log.info("count_driver < count_driver_sheets %s < %s" % (count_driver, count_driver_sheets))
            log.info("Duplicate Search")
            for driver in drivers_list:
                double_ds = DriverSheet.objects.filter(date=workday, driver=driver)
                if double_ds.count() > 1:
                    log.info("Duplicate double_ds deleted")
                    double_ds.first().delete()

        if count_driver == count_driver_sheets:
            log.info("count_driver = count_driver_sheets %s = %s" % (count_driver, count_driver_sheets))

    else:
        log.info("DriverSheet is exists")


def is_driver_sheet_exists(workday: WorkDaySheet) -> bool:
    driver_sheet = DriverSheet.objects.filter(date=workday, isArchive=False)
    if driver_sheet.exists():
        return True
    else:
        return False
