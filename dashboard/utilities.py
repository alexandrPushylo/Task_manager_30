import enum
from typing import Literal

from django.core.cache import cache
from django.db import models
from pydantic import BaseModel

from dashboard.assets import AcceptMode
from dashboard.models import WorkDaySheet, ApplicationMaterial
from django.db.models.query import QuerySet
from dashboard.models import ApplicationToday, ApplicationTechnic
from dashboard.schemas.application_today_schema import ApplicationTodaySchema
from dashboard.schemas.technic_sheet_schema import TechnicSheetWithTechnicSchema
from dashboard.schemas.user_schema import UserSchema
from dashboard.schemas.utils_schema import BusiestTechnicDataSchema
from dashboard.schemas.work_day_sheet_schema import WorkDaySchema
from logger import getLogger

#   ------------------------------------------------------------------------------------------------------------------


from datetime import date, datetime
import random
import dashboard.assets as ASSETS
from config.settings import USE_CACHE

import dashboard.variables as VAR

from dashboard.services.application_material import ApplicationMaterialService
from dashboard.services.application_technic import ApplicationTechnicService
from dashboard.services.application_today import ApplicationTodayService
from dashboard.services.construction_site import ConstructionSiteService
from dashboard.services.technic import TechnicService, TemplateDescService
from dashboard.services.work_day_sheet import WorkDayService
from dashboard.services.driver_sheet import DriverSheetService
from dashboard.services.technic_sheet import TechnicSheetService
from dashboard.services.user import UserService
from dashboard.services.parameter import ParameterService

#   ------------------------------------------------------------------------------------------------------------------
log = getLogger(__name__)



class Utilities:
    TODAY: date = date.today()
    NOW = lambda: datetime.now().time()
    USE_CACHE = USE_CACHE


    class CacheKeys(enum.Enum):
        pass


    @classmethod
    def get_ru_weekday(cls, _date: date) -> str | None:
        """
        Получить день недели на русском языке
        :param _date:
        :return:
        """
        if isinstance(_date, str):
            weekday = datetime.strptime(_date, '%Y-%m-%d').weekday()
        elif isinstance(_date, WorkDaySheet):
            weekday = _date.date
        elif isinstance(_date, date):
            weekday = _date.weekday()
        else:
            return None
        if weekday in range(0, 7):
            return ASSETS.WEEKDAY[weekday]
        else:
            return None


    @classmethod
    def get_prepared_data(cls,
                      context: dict,
                      current_workday: WorkDaySchema
                      ) -> dict:
        """
        Подготовка и получения глобальных данных
        :param context:
        :param current_workday:
        :return:
        """
        context['work_days'] = WorkDayService.get_range_of_workdays_with_weekdays(
            cls.TODAY, 1, 3, short_weekdays=True, revers=True
        )
        context['today'] = cls.TODAY
        context['current_weekday'] = cls.get_ru_weekday(cls.TODAY)
        context['prev_work_day'] = WorkDayService.get_prev_workday(current_workday.date)
        context['next_work_day'] = WorkDayService.get_next_workday(current_workday.date)
        context['weekday'] = cls.get_ru_weekday(current_workday.date)
        context['VIEW_MODE'] = cls.get_view_mode(current_workday.date)
        context['ACCEPT_MODE'] = cls.get_accept_mode_by_date(workday=current_workday)
        context['current_day'] = current_workday
        return context


    @classmethod
    def prepare_sheets(cls, workday_data: WorkDaySchema):
        cls.prepare_driver_sheet(workday_data=workday_data)
        cls.prepare_technic_sheet(workday_data=workday_data)
        log.info("Prepare sheets done")


    @classmethod
    def prepare_driver_sheet(cls, workday_data: WorkDaySchema):
        """
        Подготовка driver_sheets (prepare_driver_sheet)
        Копирование или создание записей, удаление дубликатов.
        :param workday_data:
        :return:
        """
        driver_sheets = DriverSheetService.get_queryset(
            date__date=workday_data.date,
            isArchive=False
        )
        count_driver_sheets = driver_sheets.count()

        driver_list = UserService.get_driver_list()
        count_drivers = len(driver_list)

        if count_drivers != count_driver_sheets:
            log.info("DriverSheet is not ready")

            if count_drivers > count_driver_sheets:
                log.info(f"count_driver > count_driver_sheets {count_drivers} > {count_driver_sheets}")

                last_workday_sheet = WorkDayService.get_prev_workday(workday_data.date)
                last_driver_sheet = DriverSheetService.get_queryset(
                    date_id=last_workday_sheet.id,
                    isArchive=False
                )
                count_last_driver_sheet = last_driver_sheet.count()
                if count_last_driver_sheet == count_drivers:    # COPY
                    log.info("last_driver_sheet.exists() is True - COPY")

                    new_driver_sheet = [
                        DriverSheetService.model(
                            date_id=workday_data.id,
                            driver=ds.driver,
                            status=ds.status
                        ) for ds in last_driver_sheet
                    ]
                else:   # CREATE
                    log.info("last_driver_sheet.exists() is False - CREATE")
                    exclude_drivers = driver_sheets.values_list('driver_id', flat=True)
                    new_driver_sheet = [
                        DriverSheetService.model(
                            date_id=workday_data.id,
                            driver_id=drv.id
                        ) for drv in driver_list if drv.id not in exclude_drivers
                    ]
                DriverSheetService.model.objects.bulk_create(new_driver_sheet)
            if count_driver_sheets != 0 and count_drivers != count_driver_sheets:   #Delete duplicate
                log.info(f"count_driver < count_driver_sheets {count_drivers} < {count_driver_sheets}")
                log.info("Duplicate Search")
                list_ids_for_delete = []
                for drv in driver_list:
                    double_ds = DriverSheetService.get_queryset(
                        date_id=workday_data.id,
                        driver_id=drv.id
                    )
                    if double_ds.count() > 1:
                        list_ids_for_delete.append(double_ds.first().id)
                DriverSheetService.get_queryset(id__in=list_ids_for_delete).delete()
                log.info("Duplicate double_ds deleted")
            if count_drivers == count_driver_sheets:
                log.info(f"count_driver = count_driver_sheets {count_drivers} = {count_driver_sheets}")
            cache.delete(f"{DriverSheetService.CacheKeys.DRIVER_SHEET_FOR_DAY.value}:{workday_data.date}")
        else:
            log.info("DriverSheet is exists")

    @classmethod
    def prepare_technic_sheet(cls, workday_data: WorkDaySchema):
        """
        Подготовка technic_sheets (prepare_technic_sheets)
        Копирование или создание записей, удаление дубликатов.
        :param workday_data:
        :return:
        """
        technic_sheet = TechnicSheetService.get_queryset(
            isArchive=False,
            date_id=workday_data.id
        )
        count_technic_sheet = technic_sheet.count()

        technics_list = TechnicService.get_all_technic_data()
        count_technics = len(technics_list)

        cls.autocomplete_driver_from_technic_sheet(workday_data=workday_data)

        if count_technics != count_technic_sheet:
            log.info("TechnicSheet is not ready")

            driver_sheet_list = DriverSheetService.get_queryset(
                isArchive=False,
                date_id=workday_data.id
            )

            last_workday_sheet = WorkDayService.get_prev_workday(workday_data.date)
            last_technic_sheet = TechnicSheetService.get_queryset(
                date_id=last_workday_sheet.id,
                isArchive=False
            )

            if count_technics > count_technic_sheet:
                log.info(f"count_technics > count_technic_sheet {count_technics} > {count_technic_sheet}")

                if last_technic_sheet.count() == count_technics:  # COPY
                    log.info("last_technic_sheet.exists() is True - COPY")

                    new_technic_sheet = []
                    for l_ts in last_technic_sheet:
                        if l_ts.driver_sheet:
                            driver_sheet = driver_sheet_list.filter(driver=l_ts.driver_sheet.driver).first()
                        else:
                            driver_sheet = None
                        new_technic_sheet.append(
                            TechnicSheetService.model(
                                technic=l_ts.technic,
                                driver_sheet=driver_sheet,
                                date_id=workday_data.id,
                                status=l_ts.status
                            )
                        )

                else:  # CREATE
                    log.info("last_technic_sheet.exists() is False - CREAT")

                    excludes_technic_sheet_ids = technic_sheet.values_list('technic_id', flat=True)

                    new_technic_sheet = [TechnicSheetService.model(
                        technic_id=technic.id,
                        driver_sheet=driver_sheet_list.filter(driver_id=technic.attached_driver).first(),
                        date_id=workday_data.id)
                        for technic in technics_list
                        if technic.id not in excludes_technic_sheet_ids]

                TechnicSheetService.model.objects.bulk_create(new_technic_sheet)

            if count_technic_sheet != 0 and count_technics != count_technic_sheet:  # Delete duplicate
                log.info(f"count_technics < count_technic_sheet {count_technics} < {count_technic_sheet}")
                log.info("Duplicate Search")
                list_ids_for_delete = []
                for technic in technics_list:
                    double_ts = technic_sheet.filter(date_id=workday_data.id, technic=technic)
                    if double_ts.count() > 1:
                        list_ids_for_delete.append(double_ts.first().id)
                TechnicSheetService.get_queryset(id__in=list_ids_for_delete).delete()
                log.info(f"Duplicate was deleted")
            if count_technics == count_technic_sheet:
                log.info("count_technics = count_technic_sheet %s = %s" % (count_technics, count_technic_sheet))
            cache.delete(f"{TechnicSheetService.CacheKeys.TECH_SHEET_FOR_DAY.value}:{workday_data.date}")
            cache.delete(f"{TechnicSheetService.CacheKeys.WORKLOAD_LIST.value}:{workday_data.id}")
        else:
            log.info(f"TechnicSheet for exists")


    @classmethod
    def change_driver_for_technic_sheet(cls, technic_sheet_id, driver_sheet_id) -> bool | None:
        if not driver_sheet_id or driver_sheet_id == '':
            ds = None
        else:
            ds = DriverSheetService.get_object(id=driver_sheet_id)
        ts = TechnicSheetService.get_object(id=technic_sheet_id)
        ts.driver_sheet = ds
        ts.save(update_fields=['driver_sheet'])
        cache.delete(f"{TechnicSheetService.CacheKeys.WORKLOAD_LIST.value}:{ts.date.id}")
        cache.delete(f"{TechnicSheetService.CacheKeys.TECH_SHEET_FOR_DAY.value}:{ts.date.date}")
        log.info("The driver has been changed for technic_sheet")
        if ds:
            return ds.status
        else:
            return None


    @classmethod
    def autocomplete_driver_from_technic_sheet(cls, workday_data: WorkDaySchema):
        """
        Авто подстановка закрепленного водителя
        :param workday_data:
        :return:
        """
        empty_technic_sheet = (
            TechnicSheetService
            .get_queryset(
                date_id=workday_data.id,
                isArchive=False,
                driver_sheet__isnull=True,
                technic__attached_driver__isnull=False
            )
            .select_related('driver_sheet', 'technic__attached_driver'))

        if empty_technic_sheet.exists():
            log.info("empty_technic_sheet.exists() is True")
            driver_sheet_list = DriverSheetService.get_queryset(
                isArchive=False,
                status=True,
                date_id=workday_data.id
            ).select_related('driver')

            for e_ts in empty_technic_sheet:
                _ts = TechnicSheetService.get_queryset(
                    date_id=workday_data.id,
                    driver_sheet__driver=e_ts.technic.attached_driver
                ).select_related('driver_sheet__driver', 'technic__attached_driver')
                _ds = driver_sheet_list.filter(driver=e_ts.technic.attached_driver)
                if _ts.count() == 0:
                    e_ts.driver_sheet = _ds.first()
                    e_ts.save(update_fields=['driver_sheet'])
        else:
            log.info("empty_technic_sheet.exists() is False")


    @classmethod
    def calculate_count_app_for_technic_sheet(cls, technic_sheet_id, exclude_app_tech_list: list = None) -> int:
        ts = TechnicSheetService.get_object(id=technic_sheet_id)
        app_tech = ApplicationTechnicService.get_queryset(
            technic_sheet=ts,
            isChecked=False,
            isArchive=False,
            is_cancelled=False
        )
        if exclude_app_tech_list:
            count_app_tech = app_tech.exclude(application_today__id=exclude_app_tech_list).count()
        else:
            count_app_tech = app_tech.count()
        ts.count_application = count_app_tech
        ts.save(update_fields=['count_application'])
        return count_app_tech


    @classmethod
    def calculate_all_app_for_technic_sheet(cls, ids_list: list[int], **kwargs):
        ts_list = TechnicSheetService.get_queryset(
            id__in=ids_list,
            isArchive=False
        )
        for ts in ts_list:
            cls.calculate_count_app_for_technic_sheet(technic_sheet_id=ts.id, **kwargs)


    @classmethod
    def get_ids_list_from_model(cls, model: models.Model | QuerySet[models.Model]) -> list[int]:
        if isinstance(model, models.Model):
            return [model.pk]
        elif isinstance(model, QuerySet):
            return list(model.values_list('id', flat=True))
        else:
            return []


    @classmethod
    def get_busiest_technic_title(cls, workday_data: WorkDaySchema) -> list[BusiestTechnicDataSchema]:
        """
        Получения списка с информацией о загруженности technic_title
        :param workday_data:
        :return: [{}, {}]
        """
        exclude_app_today_status = [
            ASSETS.ApplicationTodayStatus.SAVED.title,
            ASSETS.ApplicationTodayStatus.ABSENT.title,
            ASSETS.ApplicationTodayStatus.DELETED.title
        ]

        technic_sheet = TechnicSheetService.get_queryset(
            date_id=workday_data.id,
            driver_sheet__isnull=False,
            status=True,
            isArchive=False
        ).exclude(
            applicationtechnic__application_today__status__in=exclude_app_today_status
        ).values(
            'id',
            'technic',
            'technic__title',
            'driver_sheet',
            'driver_sheet__status',
            'status',
            'date',
            'count_application',
            'isArchive'
        )

        technic_sheet_data = [TechnicSheetWithTechnicSchema(**ts) for ts in technic_sheet]
        distinct_tech_title = set([ts.technic__title for ts in technic_sheet_data])
        out: list[BusiestTechnicDataSchema] = []
        for t_title in distinct_tech_title:
            ts_title = [ts for ts in technic_sheet_data if ts.technic__title == t_title and ts.driver_sheet__status]
            free_ts_title = [ts for ts in ts_title if ts.count_application==0]

            total_technic_sheet_count = len(ts_title)
            free_technic_sheet_count = len(free_ts_title)
            id_list = [ts.id for ts in ts_title]
            all_applications_count = sum([ts.count_application for ts in ts_title])
            need_technics_count = all_applications_count - total_technic_sheet_count
            out.append(BusiestTechnicDataSchema(
                technic_title=t_title,
                free_technic_sheet_count=free_technic_sheet_count,
                total_technic_sheet_count=total_technic_sheet_count,
                id_list=id_list,
                all_applications_count=all_applications_count,
                need_technics_count=need_technics_count,
            ))
        return out


    @classmethod
    def get_conflict_list_of_technic_sheet(
            cls,
            busiest_technic_title: list[BusiestTechnicDataSchema],
            priority_id_list: set,
            get_only_id_list=False) -> list[BusiestTechnicDataSchema | int]:
        """
        Получить список конфликтов technic_sheet
        :param busiest_technic_title: список с информацией о загруженности technic_title
        :param priority_id_list: сет technic_sheet_id с нераспределенным приоритетом
        :param get_only_id_list: True - получить только id; False - получить более подробную информацию
        :return: [{}, {}, ...]
        """
        out: list[BusiestTechnicDataSchema | int] = []
        for busiest_tt in busiest_technic_title:
            if busiest_tt.need_technics_count > 0 and set(busiest_tt.id_list).intersection(priority_id_list):
                if get_only_id_list:
                    out.extend(busiest_tt.id_list)
                else:
                    out.append(busiest_tt)
        return out


    @classmethod
    def get_priority_ids_list(cls, workday_data: WorkDaySchema) -> set:
        """
        Получения сета technic_sheet_id с нераспределенным приоритетом
        :param workday_data:
        :return: set(.., ...)
        """
        exclude_app_today_status = [
            ASSETS.ApplicationTodayStatus.SAVED.title,
            ASSETS.ApplicationTodayStatus.ABSENT.title,
            ASSETS.ApplicationTodayStatus.DELETED.title
        ]

        technic_sheet_ids = TechnicSheetService.get_queryset(
            date_id=workday_data.id,
            driver_sheet__isnull=False,
            status=True,
            isArchive=False,
            count_application__gt=0,
            driver_sheet__status=True
        ).exclude(
            applicationtechnic__application_today__status__in=exclude_app_today_status
        ).values('id')

        app_technic_list = list(ApplicationTechnicService.get_queryset(
            technic_sheet__in=technic_sheet_ids,
            isArchive=False,
            is_cancelled=False,
            isChecked=False
        ).values('technic_sheet__id', 'priority'))

        return set(item['technic_sheet__id'] for item in app_technic_list if app_technic_list.count(item)>1)


    @classmethod
    def set_color_for_list(cls, some_list: list) -> dict:
        """
        Привязка цвета для каждого элемента из списка some_list
        :param some_list:
        :return:
        """
        colors = ASSETS.COLORS[:]
        random.shuffle(colors)
        out = {
            int(id_): color
            for id_, color in zip(some_list, colors)
        }
        return out


    @classmethod
    def sort_applications_by_status(cls, item):
        """
        Сортировка application_today по статусу
        :param item:
        :return:
        """
        if item is None or item['application_today'] is None:
            return 10

        status = item['application_today']['status']

        if status == ASSETS.ApplicationTodayStatus.SAVED.title:
            return 1
        if status == ASSETS.ApplicationTodayStatus.SUBMITTED.title:
            return 5
        if status == ASSETS.ApplicationTodayStatus.APPROVED.title:
            return 5
        if status == ASSETS.ApplicationTodayStatus.SEND.title:
            return 5
        if status == ASSETS.ApplicationTodayStatus.DELETED.title:
            return 7
        if status == ASSETS.ApplicationTodayStatus.ABSENT.title:
            return 9
        return 9


    @classmethod
    def accept_app_tech_to_supply(cls, application_technic_id: int, application_today_id: int):
        """
        Принять заявку ApplicationTechnic(id=app_tech_id) для supply
        :param application_technic_id:
        :param application_today_id:
        :return:
        """
        application_technic = ApplicationTechnicService.get_object(id=application_technic_id)
        application_today = ApplicationTodayService.get_object(id=application_today_id)
        if all((application_technic, application_today)):

            if application_technic.is_cancelled:
                application_technic.is_cancelled = False
                application_technic.description = application_technic.description.replace(
                    ASSETS.MessagesAssets.reject.value, "")
                TechnicSheetService.increment_count_application(application_technic.technic_sheet)
                application_technic.technic_sheet.save()
                application_technic.save()

            cs_address = application_technic.application_today.construction_site.address
            cs_foreman = application_technic.application_today.construction_site.foreman
            cs_foreman__last_name = cs_foreman.last_name if cs_foreman is not None else None

            str_constr_site = f"> {cs_address} {'('+cs_foreman__last_name+')' if cs_foreman__last_name else ''}:\n".upper()
            str_desc = str_constr_site + application_technic.description + '\n'

            if not application_technic.isChecked:
                _new_app_tech, created = ApplicationTechnicService.get_or_create(
                    technic_sheet=application_technic.technic_sheet,
                    application_today=application_today
                )
                _new_app_tech.description = _new_app_tech.description + str_desc if _new_app_tech.description else str_desc
                _new_app_tech.save()

                application_technic.isChecked = True
                application_technic.id_orig_app = _new_app_tech.id
                application_technic.save()
                cls.calculate_count_app_for_technic_sheet(application_technic.technic_sheet_id)

            elif application_technic.isChecked:
                _supply_at = ApplicationTechnicService.get_object(
                    id=application_technic.id_orig_app
                )
                _supply_at.description = _supply_at.description.replace(str_desc, '')
                _supply_at.save()
                if not _supply_at.description:
                    _supply_at.delete()
                application_technic.isChecked = False

                application_technic.id_orig_app = None
                application_technic.save()
                cls.calculate_count_app_for_technic_sheet(application_technic.technic_sheet_id)
            cache.delete(f"{ApplicationTechnicService.CacheKeys.APP_TECH_FOR_DATE.value}:{application_today.date.date}")


    @classmethod
    def get_table_working_technic_sheet(cls, workday_data: WorkDaySchema):  #TODO ??????????
        """
        Получить таблицу загруженность для dashboard
        :param workday_data:
        :return:
        """
        _technic_sheet = (TechnicSheetService.get_queryset(
            isArchive=False,
            date_id=workday_data.id
        ).order_by(
            'driver_sheet__driver__last_name'
        )).select_related(
            'driver_sheet__driver', 'technic__attached_driver'
        )
        return _technic_sheet


    @classmethod
    def change_view_props(cls, io_name: str, io_status: str, io_value: str, user_id: int) -> bool:
        user = UserService.get_object(id=user_id)
        if user:
            if io_status == 'true':
                status = True
            elif io_status == 'false':
                status = False
            else:
                status = None

            if status is not None:
                cache.delete(f"{UserService.CacheKeys.CURRENT_USER.value}:{user.pk}")
                match io_name:
                    case 'is_show_deleted_app':
                        user.is_show_deleted_app = status
                        user.save(update_fields=['is_show_deleted_app'])
                        return True
                    case 'is_show_saved_app':
                        user.is_show_saved_app = status
                        user.save(update_fields=['is_show_saved_app'])
                        return True
                    case 'is_show_absent_app':
                        user.is_show_absent_app = status
                        user.save(update_fields=['is_show_absent_app'])
                        return True
                    case 'is_show_technic_app':
                        user.is_show_technic_app = status
                        user.save(update_fields=['is_show_technic_app'])
                        return True
                    case 'is_show_material_app':
                        user.is_show_material_app = status
                        user.save(update_fields=['is_show_material_app'])
                        return True
                    case 'io_color_title':
                        color = io_value if io_value is not None else '#000000'
                        user.color_title = color
                        user.save(update_fields=['color_title'])
                        return True
                    case 'io_font_size':
                        if io_value == '' or io_value is None:
                            font_size = 10
                        else:
                            try:
                                font_size = int(io_value)
                            except Exception as e:
                                log.error(f"set_data_for_filter(): 'font_size' | {e}")
                                font_size = 10
                        user.font_size = font_size
                        user.save(update_fields=['font_size'])
                        return True
                    case _:
                        return False
            return False
        return False


    @classmethod
    def set_data_for_filter(cls, request):
        """
        Установка параметров фильтрации
        :param request:
        :return:
        """

        filter_construction_site = request.POST.get('filter_construction_site')
        filter_construction_site = filter_construction_site if filter_construction_site is not None else 0

        filter_foreman = request.POST.get('filter_foreman')
        filter_foreman = filter_foreman if filter_foreman is not None else 0

        filter_technic = request.POST.get('filter_technic')
        filter_technic = filter_technic if filter_technic != '' else None

        sort_by = request.POST.get('sort_by')
        sort_by = sort_by if sort_by != '' else None

        _user = UserService.get_object(id=request.user.id)
        if _user:

            if filter_construction_site is not None:
                _user.filter_construction_site = filter_construction_site
            if filter_foreman is not None:
                _user.filter_foreman = filter_foreman

            _user.filter_technic = filter_technic
            _user.sort_by = sort_by
            _user.save()
            cache.delete(f"{UserService.CacheKeys.CURRENT_USER.value}:{_user.pk}")


    @classmethod
    def prepare_data_for_filter(cls, context: dict) -> dict:
        """
        Подготовка и получения данных для фильтра
        :param context:
        :return:
        """
        foreman_list = UserService.get_foreman_list()
        construction_site_list = [
            cs.model_dump() for cs in ConstructionSiteService.get_active_cs_list()
            if cs.status
        ]
        for cs in construction_site_list:
            foreman = list(filter(lambda f: f.id == cs["foreman"], foreman_list))
            cs["foreman"] = foreman.pop() if foreman else None
        distinct_tech_title = TechnicService.get_distinct_technic_title()
        sort_by_list = ASSETS.SORT_BY

        context['filter_foreman_list'] = foreman_list
        context['filter_construction_site_list'] = construction_site_list
        context['filter_technic_list'] = distinct_tech_title
        context['sort_by_list'] = sort_by_list
        return context


    @classmethod
    def copy_application_to_target_day(
            cls,
            application_today_id: int,
            target_workday_data: WorkDaySchema,
            default_status: str = ASSETS.ApplicationTodayStatus.SAVED.title):
        """
        Копирование заявки ApplicationToday(id=id_application_today) на _target_day
        :param target_day_id:
        :param application_today_id:
        :param default_status: saved | submitted
        :return:
        """

        current_application = ApplicationTodayService.get_object(id=application_today_id)
        new_application, _ = ApplicationTodayService.get_or_create(
            date_id=target_workday_data.id,
            # status=default_status,
            description=current_application.description,
            construction_site=current_application.construction_site
        )
        new_application.status = default_status
        new_application.isArchive = False
        new_application.save()


        current_application_material = ApplicationMaterialService.get_queryset(
            application_today=current_application
        )
        if current_application_material.exists():
            new_application_material, _ = ApplicationMaterial.objects.get_or_create(application_today=new_application)
            new_application_material.description = current_application_material.first().description
            new_application_material.save()
            cache.delete(f"{ApplicationMaterialService.CacheKeys.APP_MAT_FOR_DATE.value}:{target_workday_data.date}")

        current_application_technic = ApplicationTechnicService.get_queryset(
            application_today=current_application
        ).select_related("technic_sheet__technic")

        for tech_app in current_application_technic:
            if tech_app.technic_sheet:
                target_technic_sheet = TechnicSheetService.get_object(
                    date_id=target_workday_data.id,
                    status=True,
                    isArchive=False,
                    technic=tech_app.technic_sheet.technic)

                if target_technic_sheet:
                    new_app_tech, _ = ApplicationTechnic.objects.get_or_create(
                        application_today=new_application,
                        technic_sheet=target_technic_sheet)
                    new_app_tech.description = tech_app.description
                    new_app_tech.save()
                    TechnicSheetService.increment_count_application(target_technic_sheet)
                    cls.calculate_count_app_for_technic_sheet(target_technic_sheet.id)

        cache.delete(f"{TechnicSheetService.CacheKeys.TECH_SHEET_FOR_DAY.value}:{target_workday_data.date}")
        cache.delete(f"{ApplicationTechnicService.CacheKeys.APP_TECH_FOR_DATE.value}:{target_workday_data.date}")
        cache.delete(f"{ApplicationTodayService.CacheKeys.APPLICATIONS_TODAY_FOR_DATE.value}:{target_workday_data.date}")



    @classmethod
    def set_spec_task(cls, technic_sheet_id: int):
        """
        Отправить technic_sheet в спец. объект и назначить спец. задание по умолчанию
        :param technic_sheet_id:
        :return:
        """
        construction_site = ConstructionSiteService.get_spec_construction_site()

        technic_sheet = TechnicSheetService.get_object(id=technic_sheet_id)
        current_day = technic_sheet.date
        application_today, _ = ApplicationTodayService.get_or_create(
            construction_site=construction_site,
            date=current_day)

        application_technic, at_created = ApplicationTechnicService.get_or_create(
            application_today=application_today,
            technic_sheet=technic_sheet)
        if at_created or application_technic.isArchive or application_technic.is_cancelled:
            TechnicSheetService.increment_count_application(technic_sheet)

        template_description = TemplateDescService.get_description_mode_for_spec_app(technic_sheet.technic.id)
        description = ''
        match template_description:
            case ASSETS.TaskDescriptionMode.DEFAULT:
                description = ParameterService.get_object(
                    name=VAR.VAR_TASK_DESCRIPTION_FOR_SPEC_CONSTR_SITE['name']
                ).value
            case ASSETS.TaskDescriptionMode.MANUAL:
                description = TemplateDescService.get_object(
                    technic__id=technic_sheet.technic.id).description
            case ASSETS.TaskDescriptionMode.AUTO:
                prev_workday = WorkDayService.get_prev_workday(current_day.date)
                task_description = ApplicationTechnicService.get_queryset(
                    application_today__construction_site__address=ASSETS.MessagesAssets.CS_SPEC_TITLE.value,
                    application_today__date_id=prev_workday.id,
                    technic_sheet__technic=technic_sheet.technic,
                )
                if task_description.exists():
                    description = task_description.first().description
                else:
                    description = ''
            case _:
                description = ''
        application_technic.isArchive = False
        application_technic.is_cancelled = False
        application_technic.description = description
        application_technic.save()
        application_today.status = ASSETS.ApplicationTodayStatus.SUBMITTED.title
        application_today.save(update_fields=['status'])
        cache.delete(f"{ApplicationTodayService.CacheKeys.APPLICATIONS_TODAY_FOR_DATE.value}:{current_day.date}")
        cache.delete(f"{ApplicationTechnicService.CacheKeys.APP_TECH_FOR_DATE.value}:{current_day.date}")

    @classmethod
    def get_view_mode(cls, date_: date) -> str:
        """
        Получить режим отображения
        :param date_:
        :return:
        """
        if date_ == cls.TODAY:
            return ASSETS.ViewMode.CURRENT.value
        elif date_ < cls.TODAY:
            return ASSETS.ViewMode.ARCHIVE.value
        elif date_ > cls.TODAY:
            return ASSETS.ViewMode.FUTURE.value
        else:
            return 'None'

    @classmethod
    def get_accept_mode_by_date(cls, workday: WorkDaySchema) -> bool:
        """
        Получить режим accept mode
        True - заявки принимаются
        False - заявки не принимаются
        :param workday:
        :return:
        """

        var_time_recept_apps = ParameterService.get_object(
            name=VAR.VAR_TIME_RECEPTION_OF_TECHNICS['name']
        )
        if var_time_recept_apps:
            if workday.accept_mode == ASSETS.AcceptMode.AUTO.value:
                if var_time_recept_apps.time < datetime.now().time():
                    return True
                else:
                    return False
            elif workday.accept_mode == ASSETS.AcceptMode.MANUAL.value:
                return True
            elif workday.accept_mode == ASSETS.AcceptMode.OFF.value:
                return False

    @classmethod
    def get_accept_mode(cls, accept_mode: str) -> Literal[AcceptMode.AUTO, AcceptMode.MANUAL, AcceptMode.OFF] | None:
        """ Получить режим accept mode"""
        if accept_mode == ASSETS.AcceptMode.AUTO.value:
            return ASSETS.AcceptMode.AUTO
        elif accept_mode == ASSETS.AcceptMode.MANUAL.value:
            return ASSETS.AcceptMode.MANUAL
        elif accept_mode == ASSETS.AcceptMode.OFF.value:
            return ASSETS.AcceptMode.OFF

    @classmethod
    def set_accept_mode(cls, workday_data: WorkDaySchema, mode: ASSETS.AcceptMode):
        """
        Установить режим accept mode
        :param workday_data:
        :param mode:
        :return:
        """
        workday_instance = WorkDayService.get_object(id=workday_data.id)
        if workday_instance:
            workday_instance.accept_mode = mode.value
            workday_instance.save(update_fields=['accept_mode'])
            cache.delete(f"{WorkDayService.CacheKeys.CURRENT_DATE_DATA.value}:{workday_data.date}")
            cache.delete(f"{WorkDayService.CacheKeys.RANGE_WORKDAYS.value}")

    @classmethod
    def is_valid_get_request(cls, value: str | None) -> bool:
        """
        Проверка : value is not None and value != ''
        :param value:
        :return:
        """
        if value is not None and value != '':
            return True
        else:
            return False

    @classmethod
    def change_up_status_for_application_today(
            cls,
            workday_data: WorkDaySchema,
            application_today_id=None,
            current_status=None
    ) -> str:
        """
        Изменить статус заявки на следующий статус
        :param workday_data:
        :param application_today_id:
        :param current_status:
        :return:
        """
        if application_today_id:
            application_today = ApplicationTodayService.get_object(id=application_today_id)
            ApplicationTodayService.set_next_status(application_today)
            return application_today.status
        else:
            application_today_list = ApplicationTodayService.get_queryset(
                isArchive=False,
                date_id=workday_data.id,
                status=current_status
            )
            [ApplicationTodayService.set_next_status(application_today, False)
             for application_today in application_today_list]
            cache.delete(
                f"{ApplicationTodayService.CacheKeys.APPLICATIONS_TODAY_FOR_DATE.value}:{workday_data.date}"
            )
            if application_today_list.exists():
                return application_today_list.first().status
            else:
                return current_status

    @classmethod
    def get_status_lists_of_apps_today(cls, applications_today: list[ApplicationTodaySchema]) -> dict:
        """
        Получить сгруппированный по статусам dict с id объектами ApplicationToday
        :param applications_today:
        :return: {absent: [], saved: [], submitted: [], approved: [], send: []}
        """
        status_lists: dict[str, list] = {
            ASSETS.ApplicationTodayStatus.ABSENT.title: [],
            ASSETS.ApplicationTodayStatus.SAVED.title: [],
            ASSETS.ApplicationTodayStatus.SUBMITTED.title: [],
            ASSETS.ApplicationTodayStatus.APPROVED.title: [],
            ASSETS.ApplicationTodayStatus.SEND.title: []
        }

        for app in applications_today:
            if app.status == ASSETS.ApplicationTodayStatus.ABSENT.title:
                status_lists[ASSETS.ApplicationTodayStatus.ABSENT.title].append(app.id)
            elif app.status == ASSETS.ApplicationTodayStatus.SAVED.title:
                status_lists[ASSETS.ApplicationTodayStatus.SAVED.title].append(app.id)
            elif app.status == ASSETS.ApplicationTodayStatus.SUBMITTED.title:
                status_lists[ASSETS.ApplicationTodayStatus.SUBMITTED.title].append(app.id)
            elif app.status == ASSETS.ApplicationTodayStatus.APPROVED.title:
                status_lists[ASSETS.ApplicationTodayStatus.APPROVED.title].append(app.id)
            elif app.status == ASSETS.ApplicationTodayStatus.SEND.title:
                status_lists[ASSETS.ApplicationTodayStatus.SEND.title].append(app.id)
        return status_lists

    @classmethod
    def get_accept_to_change_materials_app(cls, current_workday: WorkDaySchema) -> bool:
        """
        Разрешено ли редактировать заявки на материалы
        :param current_workday:
        :return:
        """
        is_accept = False
        var_time_limit = ParameterService.get_object(
            name=VAR.VAR_TIME_RECEPTION_OF_MATERIALS['name']
        )
        if not var_time_limit:
            log.warning(
                f"Variable {VAR.VAR_TIME_RECEPTION_OF_MATERIALS['name']} \
                There is no time limit for submitting applications for materials.")
            return False

        time_limit = var_time_limit.time
        next_workday = WorkDayService.get_next_workday()

        if (current_workday == next_workday
                and cls.NOW() < time_limit):
            is_accept = True
            log.debug("get_accept_to_change_materials_app(): C1")

        elif cls.TODAY.weekday() in (4,) and current_workday.date.weekday() in (0,) and cls.NOW() < time_limit:
            is_accept = True
            log.debug("get_accept_to_change_materials_app(): C2")

        elif current_workday.date > next_workday.date:
            is_accept = True
            log.debug("get_accept_to_change_materials_app(): C3")

        return is_accept

    @classmethod
    def delete_user(cls, user_id: int):
        """
        Удаление пользователя
        :param user_id:
        :return:
        """
        user = UserService.delete(id=user_id)
        if user:
            DriverSheetService.get_queryset(driver_id=user_id, date__date__gte=cls.TODAY).delete()

    @classmethod
    def delete_technic(cls, technic_id: int):
        """
        Удаление техники
        :param technic_id:
        :return:
        """
        technic = TechnicService.delete(id=technic_id)
        if technic:
            _technic_sheet = TechnicSheetService.get_queryset(
                technic=technic,
                date__date__gte=cls.TODAY
            )
            _application_technic = ApplicationTechnicService.get_queryset(
                technic_sheet__in=_technic_sheet
            )
            _application_today = ApplicationTodayService.get_queryset(
                date__date__gte=cls.TODAY
            )

            _application_technic.delete()
            _technic_sheet.delete()

            for _app_today in _application_today:
                cls.validate_application_today(application_today=_app_today)


    @classmethod
    def delete_construction_site(cls, construction_site_id: int) -> bool:
        cs = ConstructionSiteService.delete(id=construction_site_id)
        if cs:
            app_today = ApplicationTodayService.get_queryset(
                construction_site=cs,
                date__date__gte=cls.TODAY
            )
            app_technic = ApplicationTechnicService.get_queryset(
                application_today__in=app_today
            )
            app_material = ApplicationMaterialService.get_queryset(
                application_today__in=app_today
            )
            technic_sheet_id_list = app_technic.values_list('technic_sheet', flat=True)
            Utilities.calculate_all_app_for_technic_sheet(list(technic_sheet_id_list))
            app_material.delete()
            app_technic.delete()
            app_today.delete()
            return True
        return False


    @classmethod
    def delete_application_today(cls, application_today_id: int):
        """
        Удалить application_today: ApplicationToday и деинкрементировать technic_sheet
        :param application_today_id:
        :return:
        """
        technic_sheet_id_list = ApplicationTechnicService.get_queryset(
            isArchive=False,
            application_today_id=application_today_id
        ).values_list('technic_sheet', flat=True)

        cls.calculate_all_app_for_technic_sheet(
            list(technic_sheet_id_list),
            exclude_app_tech_list=application_today_id
        )
        ApplicationTodayService.delete(id=application_today_id)

    @classmethod
    def restore_application_today(
            cls,
            application_today_id: int,
            status: Literal["deleted", "absent", "saved", "submitted", "approved", "send"]
    ):
        """
        Восстановить application_today: ApplicationToday и деинкрементировать technic_sheet
        :param application_today_id:
        :param status:
        :return:
        """
        technic_sheet_id_list = ApplicationTechnicService.get_queryset(
            isArchive=False,
            application_today_id=application_today_id
        ).values_list('technic_sheet', flat=True)
        cls.calculate_all_app_for_technic_sheet(list(technic_sheet_id_list))
        ApplicationTodayService.restore(status=status, id=application_today_id)

    @classmethod
    def get_default_status_for_apps_today(
            cls,
            current_user: UserSchema
    ) -> Literal["deleted", "absent", "saved", "submitted", "approved", "send"]:
        if cls.is_admin(current_user):
            return ASSETS.ApplicationTodayStatus.SUBMITTED.title
        elif cls.is_mechanic(current_user):
            return ASSETS.ApplicationTodayStatus.SUBMITTED.title
        else:
            return ASSETS.ApplicationTodayStatus.SAVED.title

    @classmethod
    def validate_application_today(
            cls,
            application_today: ApplicationToday,
            default_status: Literal["deleted", "absent", "saved", "submitted", "approved", "send"] | None = None
    ) -> bool:
        """
        Проверка application_today: ApplicationToday
        :param application_today: application_today: ApplicationToday
        :param default_status: save or submitted
        :return: True if application_today is valid and save, else False and delete
        """
        app_today_description: bool = application_today.description is not None and application_today.description != ''

        app_technic__is_exist = ApplicationTechnicService.is_exist(
            application_today=application_today,
            isArchive=False,
        )
        app_material__is_exist = ApplicationMaterialService.is_exist(
            application_today=application_today,
            isArchive=False,
        )

        if any((app_today_description, app_technic__is_exist, app_material__is_exist)):
            if application_today.is_edited and default_status:
                application_today.status = default_status
                application_today.is_edited = False
            application_today.save()
            cache.delete(f"{ApplicationTodayService.CacheKeys.APPLICATIONS_TODAY_FOR_DATE.value}:{application_today.date.date}")
            return True
        else:
            application_today.delete()
            cache.delete(f"{ApplicationTodayService.CacheKeys.APPLICATIONS_TODAY_FOR_DATE.value}:{application_today.date.date}")
            return False

    @classmethod
    def validate_cache_name(cls, raw_name: str) -> str:
        return raw_name.strip().replace(" ",'')

    @classmethod
    def is_admin(cls, current_user: UserSchema) -> bool:
        return ASSETS.UserPosts.ADMINISTRATOR.title == current_user.post

    @classmethod
    def is_foreman(cls, current_user: UserSchema) -> bool:
        return ASSETS.UserPosts.FOREMAN.title == current_user.post

    @classmethod
    def is_master(cls, current_user: UserSchema) -> bool:
        return ASSETS.UserPosts.MASTER.title == current_user.post

    @classmethod
    def is_driver(cls, current_user: UserSchema) -> bool:
        return ASSETS.UserPosts.DRIVER.title == current_user.post

    @classmethod
    def is_mechanic(cls, current_user: UserSchema) -> bool:
        return ASSETS.UserPosts.MECHANIC.title == current_user.post

    @classmethod
    def is_supply(cls, current_user: UserSchema) -> bool:
        return ASSETS.UserPosts.SUPPLY.title == current_user.post

    @classmethod
    def is_employee(cls, current_user: UserSchema) -> bool:
        return ASSETS.UserPosts.EMPLOYEE.title == current_user.post

    @classmethod
    def is_supply_driver(
            cls,
            current_technic_sheet_id_list: list,
            supply_technic_list_id_list: list
    ) -> bool:
        if current_technic_sheet_id_list and set(current_technic_sheet_id_list).issubset(supply_technic_list_id_list):
            return True
        else:
            return False

    @classmethod
    def get_current_day_data(cls, data_str: str | None) -> WorkDaySchema:
        """
        :param data_str:
        :return: WorkDaySchema
        """
        if data_str is None or data_str == "":
            return WorkDayService.get_current_date_data(cls.TODAY)
        else:
            return WorkDayService.get_current_date_data(data_str)
