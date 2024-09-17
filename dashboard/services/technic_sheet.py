import random

from dashboard.models import DriverSheet, WorkDaySheet, User, TechnicSheet, Technic
from django.db.models import F, QuerySet  # type: ignore
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


def get_technic_sheet_queryset(select_related: tuple = (),
                               order_by: tuple = (),
                               **kwargs) -> QuerySet[TechnicSheet]:
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


def get_technic_sheet(**kwargs) -> TechnicSheet:
    """
    :param kwargs:
    :return:
    """
    try:
        technic_sheet = TechnicSheet.objects.get(**kwargs)
        return technic_sheet
    except TechnicSheet.DoesNotExist:
        log.error('get_technic_sheet(): TechnicSheet.DoesNotExist')
        return TechnicSheet.objects.none()
    except TechnicSheet.MultipleObjectsReturned:
        log.error('get_technic_sheet(): TechnicSheet.MultipleObjectsReturned')
        return TechnicSheet.objects.none()
    except ValueError:
        log.error("get_technic_sheet() - ValueError ")
        return TechnicSheet.objects.none()


def change_status(technic_sheet_id) -> bool:
    technic_sheet = get_technic_sheet(pk=technic_sheet_id)
    if technic_sheet:
        if technic_sheet.status:
            technic_sheet.status = False
            log.info(f"technic_sheet с id {technic_sheet_id} установлен статус False")
            technic_sheet.save(update_fields=['status'])
            return False
        else:
            technic_sheet.status = True
            log.info(f"technic_sheet с id {technic_sheet_id} установлен статус True")
            technic_sheet.save(update_fields=['status'])
            return True


def change_driver(technic_sheet_id, driver_sheet_id):
    if not driver_sheet_id or driver_sheet_id == '':
        driver_sheet = None
    else:
        driver_sheet = DRIVER_SHEET_SERVICE.get_driver_sheet(id=driver_sheet_id)
    technic_sheet = get_technic_sheet(id=technic_sheet_id)
    technic_sheet.driver_sheet = driver_sheet
    technic_sheet.save(update_fields=['driver_sheet'])
    log.info("Для technic_sheet изменен водитель")
    if driver_sheet:
        return driver_sheet.status
    else:
        return None


def prepare_technic_sheets(workday: WorkDaySheet):
    """
    Подготовка technic_sheets (prepare_technic_sheets)
    Копирование или создание записей, удаление дубликатов.
    :param workday: WorkDaySheet
    :return:
    """
    # technic_sheet_list = TechnicSheet.objects.filter(isArchive=False, date=workday)
    technic_sheet_list = get_technic_sheet_queryset(isArchive=False, date=workday)
    count_technic_sheet = technic_sheet_list.count()

    technics_list = TECHNIC_SERVICE.get_technics_queryset(isArchive=False).select_related('attached_driver')
    count_technics = technics_list.count()

    autocomplete_driver_to_technic_sheet(workday=workday)

    if count_technics != count_technic_sheet:
        log.info(f"TechnicSheet на {workday.date} не готов")

        driver_sheet_list = DRIVER_SHEET_SERVICE.get_driver_sheet_queryset(isArchive=False, date=workday)

        last_workday = WORK_DAY_SERVICE.get_workday_queryset(date__lt=workday.date, status=True).first()
        last_technic_sheet = get_technic_sheet_queryset(date=last_workday, isArchive=False)

        if count_technics > count_technic_sheet:
            log.info(f"count_technics > count_technic_sheet {count_technics} > {count_technic_sheet}")

            if last_technic_sheet.count() == count_technics:  # COPY
                log.info(f"last_technic_sheet.exists() is {last_technic_sheet.exists()} - Копирование")

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

                excludes_technics = technic_sheet_list.values_list('technic_id', flat=True)

                current_technic_sheet = [TechnicSheet(
                    technic=technic,
                    driver_sheet=driver_sheet_list.filter(driver=technic.attached_driver).first(),
                    date=workday) for technic in technics_list if technic.id not in excludes_technics]

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
    technic_sheet = get_technic_sheet_queryset(date=workday, isArchive=False)
    if technic_sheet.exists():
        return True
    else:
        return False


def autocomplete_driver_to_technic_sheet(workday: WorkDaySheet):
    """
    Авто подстановка закрепленного водителя
    :param workday:
    :return:
    """
    empty_technic_sheet = get_technic_sheet_queryset(
        select_related=('driver_sheet', 'technic__attached_driver'),
        date=workday,
        isArchive=False,
        driver_sheet__isnull=True,
        technic__attached_driver__isnull=False)

    if empty_technic_sheet.exists():
        driver_sheet_list = DRIVER_SHEET_SERVICE.get_driver_sheet_queryset(
            select_related=('driver',),
            isArchive=False,
            status=True,
            date=workday)

        for technic_sheet in empty_technic_sheet:
            _technic_sheet = get_technic_sheet_queryset(
                select_related=('driver_sheet__driver', 'technic__attached_driver'),
                date=workday,
                driver_sheet__driver=technic_sheet.technic.attached_driver
            )
            driver_sheet = driver_sheet_list.filter(driver=technic_sheet.technic.attached_driver)
            if _technic_sheet.count() == 0:
                technic_sheet.driver_sheet = driver_sheet.first()
                technic_sheet.save()


def decrement_technic_sheet_list(technic_sheet_id_list,  **kwargs):
    """
    Декремент количества заявок на технику для каждого из technic_sheet_list
    :param technic_sheet_id_list:
    :return:
    """
    if technic_sheet_id_list:
        technic_sheet = get_technic_sheet_queryset(pk__in=technic_sheet_id_list)
        # for tech_sheet in technic_sheet:
        #     calculate_count_applications(tech_sheet.id)
        #     tech_sheet.decrement_count_application()

        for technic_sheet_id in technic_sheet_id_list:
            calculate_count_applications(technic_sheet_id, **kwargs)


def get_workload_dict_of_technic_sheet(workday: WorkDaySheet) -> dict:
    """
    Получить dict загруженности technic_sheet за workday
    :param workday: WorkDaySheet
    :return: {'id',
        'technic__title',
        'driver_sheet_id',
        'count_application'}
    """
    technic_sheet = (get_technic_sheet_queryset(
        isArchive=False,
        status=True,
        date=workday,
        driver_sheet__isnull=False,
        driver_sheet__status=True
    ).select_related(
        'driver_sheet',
        'technic'
    ).values(
        'id',
        'technic__title',
        'driver_sheet_id',
        'count_application'
    ))
    return technic_sheet


def get_free_list_of_technic_sheet(technic_title: str, workload_dict: dict, get_only_free: bool = True) -> list[dict]:
    """
    Получить список незанятых (get_only_free=True)
    или любых (get_only_free=False) данных technic_sheet для technic_title
    :param technic_title: Название техники
    :param workload_dict: dict загруженности technic_sheet
    :param get_only_free: True получить незанятых; False получить менее занятых
    :return: [{'id',
        'technic__title',
        'driver_sheet_id',
        'count_application'},...]
    """
    if workload_dict:
        if get_only_free:
            data_technic_sheet_list = [_item for _item in workload_dict if
                                       _item['technic__title'] == technic_title and _item['count_application'] == 0]
        else:
            data_technic_sheet_list = [_item for _item in workload_dict if
                                       _item['technic__title'] == technic_title]
        return data_technic_sheet_list
    return []


def get_least_busy_technic_sheet(free_technic_sheet_list: list[dict]) -> dict:
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
    log.error("get_least_busy_technic_sheet(): free_technic_sheet_list is empty")
    return {}


def get_some_technic_sheet(technic_title: str, workday: WorkDaySheet) -> TechnicSheet | None:
    workload_dict = get_workload_dict_of_technic_sheet(workday=workday)
    free_technic_sheet_list = get_free_list_of_technic_sheet(technic_title=technic_title, workload_dict=workload_dict)
    if free_technic_sheet_list:
        random_free_technic_sheet_list: dict = random.choice(free_technic_sheet_list)
        return get_technic_sheet(pk=random_free_technic_sheet_list['id'])
    else:
        any_technic_sheet_list = get_free_list_of_technic_sheet(
            technic_title=technic_title, workload_dict=workload_dict, get_only_free=False)
        least_busy_technic_sheet = get_least_busy_technic_sheet(any_technic_sheet_list)
        if least_busy_technic_sheet:
            return get_technic_sheet(pk=least_busy_technic_sheet['id'])
        else:
            return None
        # print(least_busy_technic_sheet)
        # return get_technic_sheet(pk=least_busy_technic_sheet['id'])


def calculate_count_applications(technic_sheet_id, exclude_app_tech=None):
    technic_sheet = get_technic_sheet(pk=technic_sheet_id)
    applications_technic = APP_TECHNIC_SERVICE.get_apps_technic_queryset(
        technic_sheet=technic_sheet,
        isChecked=False,
        isArchive=False,
        is_cancelled=False
    )
    if exclude_app_tech:
        count_applications_technic = applications_technic.exclude(application_today__id=exclude_app_tech).count()
    else:
        count_applications_technic = applications_technic.count()
    technic_sheet.count_application = count_applications_technic
    technic_sheet.save(update_fields=['count_application'])


def calculate_all_applications_for_ts(workday: WorkDaySheet):
    technic_sheet_list = get_technic_sheet_queryset(
        date=workday,
        isArchive=False,
    )
    for technic_sheet in technic_sheet_list:
        calculate_count_applications(technic_sheet.id)
