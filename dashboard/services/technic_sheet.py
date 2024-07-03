from dashboard.models import DriverSheet, WorkDaySheet, User, TechnicSheet, Technic
from django.db.models import F, QuerySet
import dashboard.assets as ASSETS
import dashboard.utilities as U
import dashboard.services.user as USERS_SERVICE
import dashboard.services.technic as TECHNIC_SERVICE
import dashboard.services.construction_site as CONSTR_SITE_SERVICE
import dashboard.services.work_day_sheet as WORK_DAY_SERVICE
import dashboard.services.driver_sheet as DRIVER_SHEET_SERVICE
import dashboard.services.dashboard as DASHBOARD_SERVICE
import dashboard.services.application_today as APP_TODAY_SERVICE
import dashboard.services.application_technic as APP_TECHNIC_SERVICE
import dashboard.services.application_material as APP_MATERIAL_SERVICE
from logger import getLogger

log = getLogger(__name__)


def change_status(technic_sheet_id):
    try:
        technic_sheet = TechnicSheet.objects.get(id=technic_sheet_id)
        if technic_sheet.status:
            technic_sheet.status = False
            log.info(f"technic_sheet с id {technic_sheet_id} установлен статус False")
        else:
            technic_sheet.status = True
            log.info(f"technic_sheet с id {technic_sheet_id} установлен статус True")
        technic_sheet.save(update_fields=['status'])
    except TechnicSheet.DoesNotExist:
        log.error(f"TechnicSheet с id {technic_sheet_id} не существует")
    except ValueError:
        log.error("change_status() - ValueError ")


def change_driver(technic_sheet_id, driver_sheet_id):
    try:
        if not driver_sheet_id or driver_sheet_id == '':
            driver_sheet = None
        else:
            driver_sheet = DriverSheet.objects.get(id=driver_sheet_id)
        technic_sheet = TechnicSheet.objects.get(id=technic_sheet_id)
        technic_sheet.driver_sheet = driver_sheet
        technic_sheet.save(update_fields=['driver_sheet'])
        log.info(f"Для technic_sheet изменен водитель")
    except TechnicSheet.DoesNotExist:
        log.error(f"TechnicSheet с id {technic_sheet_id} не существует")
    except DriverSheet.DoesNotExist:
        log.error(f"Driver_sheet с id {driver_sheet_id} не существует")
    except ValueError:
        log.error("change_driver() - ValueError ")


def prepare_technic_sheets(workday: WorkDaySheet):
    """
    Подготовка technic_sheets (prepare_technic_sheets)
    Копирование или создание записей, удаление дубликатов.
    :param workday: WorkDaySheet
    :return:
    """
    technic_sheet_list = TechnicSheet.objects.filter(isArchive=False, date=workday)
    count_technic_sheet = technic_sheet_list.count()

    technics_list = Technic.objects.filter(isArchive=False).select_related('attached_driver')
    count_technics = technics_list.count()

    autocomplete_driver_to_technic_sheet(workday=workday)

    if count_technics != count_technic_sheet:
        log.info(f"TechnicSheet на {workday.date} не готов")

        driver_sheet_list = DriverSheet.objects.filter(isArchive=False, date=workday, status=True)

        last_workday = WorkDaySheet.objects.filter(date__lt=workday.date, status=True).first()
        last_technic_sheet = TechnicSheet.objects.filter(date=last_workday, isArchive=False)

        if count_technics > count_technic_sheet:
            log.info(f"count_technics > count_technic_sheet {count_technics} > {count_technic_sheet}")

            if last_technic_sheet.exists():  # COPY
                log.info(f"last_technic_sheet.exists() is {last_technic_sheet.exists()} - Копирование")

                # current_technic_sheet = [TechnicSheet(
                #     technic=ts.technic,
                #     driver_sheet=driver_sheet_list.filter(driver=ts.driver_sheet.driver).first(),
                #     date=workday,
                #     status=ts.status) for ts in last_technic_sheet]

                current_technic_sheet = []
                for ts in last_technic_sheet:
                    if ts.driver_sheet:
                        driver_sheet = driver_sheet_list.filter(driver=ts.driver_sheet.driver).first()
                    else:
                        driver_sheet = None
                    current_technic_sheet.append(
                        TechnicSheet(
                            technic=ts.technic,
                            driver_sheet=driver_sheet,
                            date=workday,
                            status=ts.status
                        )
                    )

            else:  # CREATE
                log.info(f"last_technic_sheet.exists() is {last_technic_sheet.exists()} - Создание")

                current_technic_sheet = [TechnicSheet(
                    technic=technic,
                    driver_sheet=driver_sheet_list.filter(driver=technic.attached_driver).first(),
                    date=workday) for technic in technics_list]

            TechnicSheet.objects.bulk_create(current_technic_sheet)

        if count_technic_sheet != 0 and count_technics != count_technic_sheet:  # Delete duplicate
            log.info(f"count_technics < count_technic_sheet {count_technics} < {count_technic_sheet}")
            log.info(f"Поиск дубликата")
            for technic in technics_list:
                double_ts = technic_sheet_list.filter(date=workday, technic=technic)
                if double_ts.count() > 1:
                    log.info(f"Дубликат {double_ts.first()} удален")
                    double_ts.first().delete()

        if count_technics == count_technic_sheet:
            log.info(f"count_technics = count_technic_sheet {count_technics} = {count_technic_sheet}")

    else:
        log.info(f"TechnicSheet на {workday.date} существует")


def is_technic_sheet_exists(workday: WorkDaySheet) -> bool:
    technic_sheet = TechnicSheet.objects.filter(date=workday, isArchive=False)
    if technic_sheet.exists():
        return True
    else:
        return False


def autocomplete_driver_to_technic_sheet(workday: WorkDaySheet):
    empty_technic_sheet = TechnicSheet.objects.filter(
        date=workday,
        isArchive=False,
        driver_sheet__isnull=True,
        technic__attached_driver__isnull=False).select_related('driver_sheet', 'technic__attached_driver')

    if empty_technic_sheet.exists():
        driver_sheet_list = DriverSheet.objects.filter(
            isArchive=False,
            status=True,
            date=workday).select_related('driver')

        for technic_sheet in empty_technic_sheet:
            driver_sheet = driver_sheet_list.filter(driver=technic_sheet.technic.attached_driver
                                                    )

            if driver_sheet.count() == 1:
                technic_sheet.driver_sheet = driver_sheet.first()
                technic_sheet.save()


def get_technic_sheet_queryset(select_related: tuple = (),
                               order_by: tuple = (),
                               **kwargs) -> TechnicSheet.objects:
    """
    :param select_related:
    :param order_by:
    :param kwargs:
    :return:
    """

    technic_sheet = TechnicSheet.objects.filter(**kwargs)

    if select_related:
        technic_sheet = technic_sheet.select_related(*select_related)
    if order_by:
        technic_sheet = technic_sheet.order_by(*order_by)

    return technic_sheet


def get_technic_sheet(**kwargs) -> TechnicSheet | None:
    """
    :param kwargs:
    :return:
    """
    try:
        technic_sheet = TechnicSheet.objects.get(**kwargs)
        return technic_sheet
    except TechnicSheet.DoesNotExist:
        log.error('get_technic_sheet(): TechnicSheet.DoesNotExist')
        return None
    except TechnicSheet.MultipleObjectsReturned:
        log.error('get_technic_sheet(): TechnicSheet.MultipleObjectsReturned')
        return None


def decrement_technic_sheet_list(technic_sheet_id_list):
    """
    Декремент количества заявок на технику для каждого из technic_sheet_list
    :param technic_sheet_id_list:
    :return:
    """
    if technic_sheet_id_list:
        technic_sheet = get_technic_sheet_queryset(isArchive=False, pk__in=technic_sheet_id_list)
        technic_sheet.update(count_application=F('count_application') - 1)

def get_least_busy_technic_sheet(free_technic_sheet_list: list) -> dict:
    """
    Получить наименее занятого dict(technic_sheet)
    :param free_technic_sheet_list:
    :return: {'id',
        'technic__title',
        'driver_sheet_id',
        'count_application'}
    """
    if free_technic_sheet_list:
        least_busy_technic_sheet = sorted(free_technic_sheet_list, key=lambda item: item['count_application'])[0]
        return least_busy_technic_sheet


def get_some_technic_sheet(technic_title: str, workday: WorkDaySheet) -> TechnicSheet:
    workload_dict = get_workload_dict_of_technic_sheet(workday=workday)
    free_technic_sheet_list = get_free_list_of_technic_sheet(technic_title=technic_title, workload_dict=workload_dict)
    if free_technic_sheet_list:
        random_free_technic_sheet_list: dict = random.choice(free_technic_sheet_list)
        return get_technic_sheet(pk=random_free_technic_sheet_list['id'])
    else:
        any_technic_sheet_list = get_free_list_of_technic_sheet(
            technic_title=technic_title, workload_dict=workload_dict, get_only_free=False)
        least_busy_technic_sheet = get_least_busy_technic_sheet(any_technic_sheet_list)
        return get_technic_sheet(pk=least_busy_technic_sheet['id'])


