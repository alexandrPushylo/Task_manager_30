import enum
from typing import Literal

from django.core.cache import cache
from django.db import models
from pydantic import BaseModel

from dashboard.assets import AcceptMode
from dashboard.models import WorkDaySheet, DriverSheet, TechnicSheet, ConstructionSite, ApplicationMaterial
from django.db.models.query import QuerySet
from dashboard.models import ApplicationToday, ApplicationTechnic
from dashboard.models import User
from dashboard.schemas.application_today_schema import ApplicationTodaySchema
from dashboard.schemas.technic_sheet_schema import TechnicSheetSchema, TechnicSheetWithTechnicSchema
from dashboard.schemas.user_schema import UserSchema
from dashboard.schemas.utils_schema import BusiestTechnicDataSchema, FilterDataSchema
from dashboard.schemas.work_day_sheet_schema import WorkDaySchema
from logger import getLogger

#   ------------------------------------------------------------------------------------------------------------------


from datetime import date, datetime
import random
import dashboard.assets as ASSETS
from config.settings import USE_CACHE

import dashboard.variables as VAR
import dashboard.services.user as USERS_SERVICE
import dashboard.services.technic as TECHNIC_SERVICE
import dashboard.services.construction_site as CONSTR_SITE_SERVICE
# import dashboard.services.work_day_sheet as WORK_DAY_SERVICE
import dashboard.services.driver_sheet as DRIVER_SHEET_SERVICE
import dashboard.services.technic_sheet as TECHNIC_SHEET_SERVICE
import dashboard.services.application_today as APP_TODAY_SERVICE
import dashboard.services.application_technic as APP_TECHNIC_SERVICE
import dashboard.services.application_material as APP_MATERIAL_SERVICE
import dashboard.services.parameter as PARAMETER_SERVICE



from dashboard.services.application_material import ApplicationMaterialService
from dashboard.services.application_technic import ApplicationTechnicService
from dashboard.services.application_today import ApplicationTodayService
from dashboard.services.construction_site import ConstructionSiteService
from dashboard.services.technic import TechnicService
from dashboard.services.work_day_sheet import WorkDayService
from dashboard.services.driver_sheet import DriverSheetService
from dashboard.services.technic_sheet import TechnicSheetService
from dashboard.services.user import UserService
from dashboard.services.parameter import ParameterService

#   ------------------------------------------------------------------------------------------------------------------
log = getLogger(__name__)

# TODAY: date = date.today()
# NOW = lambda: datetime.now().time()



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
        else:
            log.info(f"TechnicSheet for exists")


    @classmethod
    def change_driver_for_technic_sheet(cls, technic_sheet_id, driver_sheet_id) -> bool | None:
        if not driver_sheet_id or driver_sheet_id == '':
            ds = None
        else:
            ds = DRIVER_SHEET_SERVICE.DriverSheetService.get_object(id=driver_sheet_id)
        ts = TECHNIC_SHEET_SERVICE.TechnicSheetService.get_object(id=technic_sheet_id)
        ts.driver_sheet = ds
        ts.save(update_fields=['driver_sheet'])
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
        ts = TECHNIC_SHEET_SERVICE.TechnicSheetService.get_object(id=technic_sheet_id)
        app_tech = APP_TECHNIC_SERVICE.ApplicationTechnicService.get_queryset(
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
        ts_list = TECHNIC_SHEET_SERVICE.TechnicSheetService.get_queryset(
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
            # driver_sheet__status=True,
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
                application_technic.technic_sheet.increment_count_application()
                application_technic.technic_sheet.save()
                application_technic.save()

            cs_address = application_technic.application_today.construction_site.address
            cs_foreman = application_technic.application_today.construction_site.foreman
            cs_foreman__last_name = cs_foreman.last_name if cs_foreman is not None else None

            str_constr_site = f"> {cs_address} {'('+cs_foreman__last_name+')' if cs_foreman__last_name else ''}:\n".upper()
            str_desc = str_constr_site + application_technic.description + '\n'

            if not application_technic.isChecked:
                # _new_app_tech, created = ApplicationTechnic.objects.get_or_create(
                _new_app_tech, created = ApplicationTechnicService.get_or_create(
                    technic_sheet=application_technic.technic_sheet,
                    application_today=application_today
                )
                _new_app_tech.description = _new_app_tech.description + str_desc if _new_app_tech.description else str_desc
                _new_app_tech.save()

                application_technic.isChecked = True
                application_technic.id_orig_app = _new_app_tech.id
                application_technic.save()
                # TECHNIC_SHEET_SERVICE.calculate_count_applications(application_technic.technic_sheet_id)
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
    def get_table_working_technic_sheet(cls, current_day_id: int):  #TODO ??????????
        """
        Получить таблицу загруженность для dashboard
        :param current_day_id:
        :return:
        """
        _technic_sheet = TECHNIC_SHEET_SERVICE.get_technic_sheet_queryset(
            select_related=('driver_sheet__driver', 'technic__attached_driver'),
            isArchive=False,
            date_id=current_day_id
        )
        return _technic_sheet.order_by('driver_sheet__driver__last_name')


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
            cs.model_dump() for cs in ConstructionSiteService.get_cs_active_list()
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
    def copy_application_to_target_day(cls,
                                       application_today_id: int,
                                       target_day_id: int,
                                       default_status: str = ASSETS.ApplicationTodayStatus.SAVED.title):
        """
        Копирование заявки ApplicationToday(id=id_application_today) на _target_day
        :param target_day_id:
        :param application_today_id:
        :param default_status: saved | submitted
        :return:
        """

        current_application = APP_TODAY_SERVICE.ApplicationTodayService.get_object(id=application_today_id)

        new_application, _ = APP_TODAY_SERVICE.ApplicationTodayService.get_or_create(
            date_id=target_day_id,
            status=default_status,
            description=current_application.description,
            construction_site=current_application.construction_site
        )

        current_application_material = APP_MATERIAL_SERVICE.ApplicationMaterialService.get_queryset(
            application_today=current_application
        )
        if current_application_material.exists():
            new_application_material, _ = ApplicationMaterial.objects.get_or_create(application_today=new_application)
            new_application_material.description = current_application_material.first().description
            new_application_material.save()

        current_application_technic = APP_TECHNIC_SERVICE.ApplicationTechnicService.get_queryset(
            application_today=current_application
        ).select_related("technic_sheet__technic")

        for tech_app in current_application_technic:
            if tech_app.technic_sheet:
                target_technic_sheet = TECHNIC_SHEET_SERVICE.get_technic_sheet(
                    date_id=target_day_id,
                    status=True,
                    isArchive=False,
                    technic=tech_app.technic_sheet.technic)

                if target_technic_sheet:
                    new_app_tech, _ = ApplicationTechnic.objects.get_or_create(
                        application_today=new_application,
                        technic_sheet=target_technic_sheet)
                    new_app_tech.description = tech_app.description
                    new_app_tech.save()
                    target_technic_sheet.increment_count_application()


    @classmethod
    def set_spec_task(cls, technic_sheet_id: int):
        """
        Отправить technic_sheet в спец. объект и назначить спец. задание по умолчанию
        :param technic_sheet_id:
        :return:
        """
        # construction_site, _ = ConstructionSite.objects.get_or_create(address=ASSETS.MessagesAssets.CS_SPEC_TITLE.value)
        construction_site = CONSTR_SITE_SERVICE.ConstructionSiteService.get_spec_construction_site()

        technic_sheet = TECHNIC_SHEET_SERVICE.TechnicSheetService.get_object(id=technic_sheet_id)
        current_day = technic_sheet.date
        # application_today, _ = ApplicationToday.objects.get_or_create(
        #     construction_site=construction_site,
        #     date=current_day)
        application_today, _ = APP_TODAY_SERVICE.ApplicationTodayService.get_or_create(
            construction_site=construction_site,
            date=current_day)

        # application_technic, at_created = ApplicationTechnic.objects.get_or_create(
        #     application_today=application_today,
        #     technic_sheet=technic_sheet)
        application_technic, at_created = APP_TECHNIC_SERVICE.ApplicationTechnicService.get_or_create(
            application_today=application_today,
            technic_sheet=technic_sheet)
        if at_created:
            technic_sheet.increment_count_application()

        template_description = TECHNIC_SERVICE.TemplateDescService.get_description_mode_for_spec_app(technic_sheet.technic.id)
        match template_description:
            case ASSETS.TaskDescriptionMode.DEFAULT:
                description = PARAMETER_SERVICE.ParameterService.get_object(
                    name=VAR.VAR_TASK_DESCRIPTION_FOR_SPEC_CONSTR_SITE['name']
                ).value
            case ASSETS.TaskDescriptionMode.MANUAL:
                description = TECHNIC_SERVICE.TemplateDescService.get_object(
                    technic__id=technic_sheet.technic.id).description
            case ASSETS.TaskDescriptionMode.AUTO:
                prev_workday = WorkDayService.get_prev_workday(current_day.date)
                task_description = APP_TECHNIC_SERVICE.ApplicationTechnicService.get_queryset(
                    application_today__construction_site__address=ASSETS.MessagesAssets.CS_SPEC_TITLE.value,
                    application_today__date=prev_workday,
                    technic_sheet__technic=technic_sheet.technic,
                )
                if task_description.exists():
                    description = task_description.first().description
                else:
                    description = ''
            case _:
                description = ''

        application_technic.description = description
        application_technic.save()
        application_today.status = ASSETS.ApplicationTodayStatus.SUBMITTED.title
        application_today.save(update_fields=['status'])

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

        var_time_recept_apps = PARAMETER_SERVICE.ParameterService.get_object(
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
            workday_id: int,
            application_today_id=None,
            current_status=None
    ) -> str:
        """
        Изменить статус заявки на следующий статус
        :param workday_id:
        :param application_today_id:
        :param current_status:
        :return:
        """
        if application_today_id:
            application_today = APP_TODAY_SERVICE.ApplicationTodayService.get_object(id=application_today_id)
            application_today.set_next_status()
            return application_today.status
        else:
            application_today_list = APP_TODAY_SERVICE.ApplicationTodayService.get_queryset(
                isArchive=False,
                date_id=workday_id,
                status=current_status
            )
            [application_today.set_next_status() for application_today in application_today_list]
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
    def get_accept_to_change_materials_app(cls, current_workday: WorkDaySheet) -> bool:
        """
        Разрешено ли редактировать заявки на материалы
        :param current_workday:
        :return:
        """
        is_accept = False
        var_time_limit = PARAMETER_SERVICE.ParameterService.get_object(
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
        user = USERS_SERVICE.UserService.delete(id=user_id)
        if user:
            DRIVER_SHEET_SERVICE.DriverSheetService.get_queryset(driver_id=user_id, date__date__gte=cls.TODAY).delete()

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
        technic_sheet_id_list = APP_TECHNIC_SERVICE.ApplicationTechnicService.get_queryset(
            isArchive=False,
            application_today_id=application_today_id
        ).values_list('technic_sheet', flat=True)

        cls.calculate_all_app_for_technic_sheet(
            list(technic_sheet_id_list),
            exclude_app_tech_list=application_today_id
        )
        APP_TODAY_SERVICE.ApplicationTodayService.delete(id=application_today_id)

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
        technic_sheet_id_list = APP_TECHNIC_SERVICE.ApplicationTechnicService.get_queryset(
            isArchive=False,
            application_today_id=application_today_id
        ).values_list('technic_sheet', flat=True)
        cls.calculate_all_app_for_technic_sheet(list(technic_sheet_id_list))
        APP_TODAY_SERVICE.ApplicationTodayService.restore(status=status, id=application_today_id)

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

        app_technic__is_exist = APP_TECHNIC_SERVICE.ApplicationTechnicService.is_exist(
            application_today=application_today,
            isArchive=False,
        )
        app_material__is_exist = APP_MATERIAL_SERVICE.ApplicationMaterialService.is_exist(
            application_today=application_today,
            isArchive=False,
        )

        if any((app_today_description, app_technic__is_exist, app_material__is_exist)):
            if application_today.is_edited and default_status:
                application_today.status = default_status
                application_today.is_edited = False
            application_today.save()
            return True
        else:
            application_today.delete()
            return False

    @classmethod
    def validate_cache_name(cls, raw_name: str) -> str:
        return raw_name.strip().replace(" ",'')

    @classmethod
    def is_admin(cls, current_user: USERS_SERVICE.UserSchema) -> bool:
        return ASSETS.UserPosts.ADMINISTRATOR.title == current_user.post

    @classmethod
    def is_foreman(cls, current_user: USERS_SERVICE.UserSchema) -> bool:
        return ASSETS.UserPosts.FOREMAN.title == current_user.post

    @classmethod
    def is_master(cls, current_user: USERS_SERVICE.UserSchema) -> bool:
        return ASSETS.UserPosts.MASTER.title == current_user.post

    @classmethod
    def is_driver(cls, current_user: USERS_SERVICE.UserSchema) -> bool:
        return ASSETS.UserPosts.DRIVER.title == current_user.post

    @classmethod
    def is_mechanic(cls, current_user: USERS_SERVICE.UserSchema) -> bool:
        return ASSETS.UserPosts.MECHANIC.title == current_user.post

    @classmethod
    def is_supply(cls, current_user: USERS_SERVICE.UserSchema) -> bool:
        return ASSETS.UserPosts.SUPPLY.title == current_user.post

    @classmethod
    def is_employee(cls, current_user: USERS_SERVICE.UserSchema) -> bool:
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


    @classmethod
    def t2(cls, t_sh__id, workday_data: WorkDaySchema):
        out = {}
        driver_sh = DriverSheetService.get_driver_sheet_for_date(workday_data)
        tech_sh = TechnicSheetService.get_tech_sheet_for_date(workday_data)
        drivers = UserService.get_all_users_list()

        cur_tech_sh = TechnicSheetService.filter_tech_sheet_by_id(t_sh__id, tech_sh)
        cur_driver_sh = DriverSheetService.filter_driver_sheet_by_id(cur_tech_sh.driver_sheet, driver_sh)
        cur_driver = UserService.filter_user_by_id_from_data(cur_driver_sh.driver, drivers)

        return cur_driver




# def convert_str_to_date(str_date: str) -> date | None:
#     """конвертация str в datetime.date"""
#     try:
#         if isinstance(str_date, str):
#             _day = datetime.strptime(str_date, '%Y-%m-%d').date()
#             return _day
#         elif isinstance(str_date, date):
#             return str_date
#     except Exception as e:
#         log.warning(f'convert_str_to_date(): {e}')





# def autocomplete_technic_sheet(technic_sheet: TechnicSheet.objects):
#     empty_technic_sheet = technic_sheet.filter(
#         driver_sheet__isnull=True,
#         technic__attached_driver__isnull=False
#     )
#     if empty_technic_sheet.exists():
#         driver_sheet_list = DriverSheet.objects.filter(isArchive=False, status=True)
#         for technic_sheet in empty_technic_sheet:
#             driver_sheet = driver_sheet_list.filter(
#                 date=technic_sheet.date,
#                 driver=technic_sheet.technic.attached_driver
#             ).first()
#             technic_sheet.driver_sheet = driver_sheet
#             technic_sheet.save()


# def decrement_all_technic_sheet(current_date: WorkDaySheet):
#     technic_sheet_list = TechnicSheet.objects.filter(isArchive=False, date=current_date)
#     for technic_sheet in technic_sheet_list:
#         technic_sheet.count_application = 0
#         technic_sheet.save(update_fields=['count_application'])


# def get_prepared_data(context: dict, current_workday: WORK_DAY_SERVICE.WorkDaySchema) -> dict:
#     """
#     Подготовка и получения глобальных данных
#     :param context:
#     :param current_workday:
#     :return:
#     """
#     # workdays = WORK_DAY_SERVICE.get_range_workdays(start_date=TODAY, before_days=1, after_days=3)[::-1]
#     # print(workdays)
#     # for workday in workdays:
#     #     workday['weekday'] = ASSETS.WEEKDAY[workday['date'].weekday()][:3]
#     # context['work_days'] = workdays
#     context['work_days'] = WORK_DAY_SERVICE.WorkDayService.get_range_of_workdays_with_weekdays(
#         TODAY, 1, 3, short_weekdays=True, revers=True
#     )
#     context['today'] = TODAY
#     context['current_weekday'] = get_ru_weekday(TODAY)
#     context['prev_work_day'] = WORK_DAY_SERVICE.WorkDayService.get_prev_workday(current_workday.date)
#     context['next_work_day'] = WORK_DAY_SERVICE.WorkDayService.get_next_workday(current_workday.date)
#     context['weekday'] = get_ru_weekday(current_workday.date)
#     context['VIEW_MODE'] = get_view_mode(current_workday.date)
#     context['ACCEPT_MODE'] = get_accept_mode_by_date(workday=current_workday)
#     return context


# def prepare_sheets(work_day: WorkDaySheet):
#     DRIVER_SHEET_SERVICE.prepare_driver_sheet(workday=work_day)
#     TECHNIC_SHEET_SERVICE.prepare_technic_sheets(workday=work_day)
#     log.info(f"{work_day.date} => Prepare sheets done")


# def prepare_driver_sheet(workday_instance: WorkDaySheet):
#     """
#     Подготовка driver_sheets (prepare_driver_sheet)
#     Копирование или создание записей, удаление дубликатов.
#     :param workday_instance:
#     :return:
#     """
#     driver_sheets = DRIVER_SHEET_SERVICE.DriverSheetService.get_queryset(
#         date=workday_instance,
#         isArchive=False
#     )
#     count_driver_sheets = driver_sheets.count()
#
#     driver_list = USERS_SERVICE.UserService.get_driver_list()
#     count_drivers = len(driver_list)
#
#     if count_drivers != count_driver_sheets:
#         log.info("DriverSheet is not ready")
#
#         if count_drivers > count_driver_sheets:
#             log.info(f"count_driver > count_driver_sheets {count_drivers} > {count_driver_sheets}")
#             last_workday_sheet = WORK_DAY_SERVICE.WorkDayService.get_queryset(
#                 date__lt=workday_instance.date,
#                 status=True
#             ).first()
#             last_driver_sheet = DRIVER_SHEET_SERVICE.DriverSheetService.get_queryset(
#                 date=last_workday_sheet,
#                 isArchive=False
#             )
#             count_last_driver_sheet = last_driver_sheet.count()
#             if count_last_driver_sheet == count_drivers:    # COPY
#                 log.info("last_driver_sheet.exists() is True - COPY")
#
#                 new_driver_sheet = [
#                     DRIVER_SHEET_SERVICE.DriverSheet(
#                         date=workday_instance,
#                         driver=ds.driver,
#                         status=ds.status
#                     ) for ds in last_driver_sheet
#                 ]
#             else:   # CREATE
#                 log.info("last_driver_sheet.exists() is False - CREATE")
#                 exclude_drivers = driver_sheets.values_list('driver_id', flat=True)
#                 new_driver_sheet = [
#                     DRIVER_SHEET_SERVICE.DriverSheet(
#                         date=workday_instance,
#                         driver_id=drv.id
#                     ) for drv in driver_list if drv.id not in exclude_drivers
#                 ]
#             DRIVER_SHEET_SERVICE.DriverSheet.objects.bulk_create(new_driver_sheet)
#         if count_driver_sheets != 0 and count_drivers != count_driver_sheets:   #Delete duplicate
#             log.info(f"count_driver < count_driver_sheets {count_drivers} < {count_driver_sheets}")
#             log.info("Duplicate Search")
#             list_ids_for_delete = []
#             for drv in driver_list:
#                 double_ds = DRIVER_SHEET_SERVICE.DriverSheetService.get_queryset(
#                     date=workday_instance,
#                     driver_id=drv.id
#                 )
#                 if double_ds.count() > 1:
#                     list_ids_for_delete.append(double_ds.first().id)
#             DRIVER_SHEET_SERVICE.DriverSheet.objects.filter(id__in=list_ids_for_delete).delete()
#             log.info("Duplicate double_ds deleted")
#         if count_drivers == count_driver_sheets:
#             log.info(f"count_driver = count_driver_sheets {count_drivers} = {count_driver_sheets}")
#     else:
#         log.info("DriverSheet is exists")

# def prepare_technic_sheet(workday_instance: WorkDaySheet):
#     """
#     Подготовка technic_sheets (prepare_technic_sheets)
#     Копирование или создание записей, удаление дубликатов.
#     :param workday_instance:
#     :return:
#     """
#     technic_sheet = TECHNIC_SHEET_SERVICE.TechnicSheetService.get_queryset(
#         isArchive=False,
#         date=workday_instance
#     )
#     count_technic_sheet = technic_sheet.count()
#
#     technics_list = TECHNIC_SERVICE.TechnicService.get_all_technic_data()
#     count_technics = len(technics_list)
#
#     autocomplete_driver_from_technic_sheet(workday_instance=workday_instance)
#
#     if count_technics != count_technic_sheet:
#         log.info("TechnicSheet is not ready")
#
#         driver_sheet_list = DRIVER_SHEET_SERVICE.DriverSheetService.get_queryset(
#             isArchive=False,
#             date=workday_instance
#         )
#
#         last_workday = WORK_DAY_SERVICE.WorkDayService.get_queryset(
#             date__lt=workday_instance.date,
#             status=True
#         ).first()
#         last_technic_sheet = TECHNIC_SHEET_SERVICE.TechnicSheetService.get_queryset(
#             date=last_workday,
#             isArchive=False
#         )
#
#         if count_technics > count_technic_sheet:
#             log.info(f"count_technics > count_technic_sheet {count_technics} > {count_technic_sheet}")
#
#             if last_technic_sheet.count() == count_technics:  # COPY
#                 log.info("last_technic_sheet.exists() is True - COPY")
#
#                 new_technic_sheet = []
#                 for l_ts in last_technic_sheet:
#                     if l_ts.driver_sheet:
#                         driver_sheet = driver_sheet_list.filter(driver=l_ts.driver_sheet.driver).first()
#                     else:
#                         driver_sheet = None
#                     new_technic_sheet.append(
#                         TechnicSheet(
#                             technic=l_ts.technic,
#                             driver_sheet=driver_sheet,
#                             date=workday_instance,
#                             status=l_ts.status
#                         )
#                     )
#
#             else:  # CREATE
#                 log.info("last_technic_sheet.exists() is False - CREAT")
#
#                 excludes_technic_sheet_ids = technic_sheet.values_list('technic_id', flat=True)
#
#                 new_technic_sheet = [TechnicSheet(
#                     technic_id=technic.id,
#                     driver_sheet=driver_sheet_list.filter(driver_id=technic.attached_driver).first(),
#                     date=workday_instance)
#                     for technic in technics_list
#                     if technic.id not in excludes_technic_sheet_ids]
#
#             TechnicSheet.objects.bulk_create(new_technic_sheet)
#
#         if count_technic_sheet != 0 and count_technics != count_technic_sheet:  # Delete duplicate
#             log.info(f"count_technics < count_technic_sheet {count_technics} < {count_technic_sheet}")
#             log.info("Duplicate Search")
#             list_ids_for_delete = []
#             for technic in technics_list:
#                 double_ts = technic_sheet.filter(date=workday_instance, technic=technic)
#                 if double_ts.count() > 1:
#                     list_ids_for_delete.append(double_ts.first().id)
#             TECHNIC_SHEET_SERVICE.TechnicSheetService.get_queryset(id__in=list_ids_for_delete).delete()
#             log.info(f"Duplicate was deleted")
#         if count_technics == count_technic_sheet:
#             log.info("count_technics = count_technic_sheet %s = %s" % (count_technics, count_technic_sheet))
#     else:
#         log.info(f"TechnicSheet for exists")

# def change_driver_for_technic_sheet(technic_sheet_id, driver_sheet_id) -> bool | None:
#     if not driver_sheet_id or driver_sheet_id == '':
#         ds = None
#     else:
#         ds = DRIVER_SHEET_SERVICE.DriverSheetService.get_object(id=driver_sheet_id)
#     ts = TECHNIC_SHEET_SERVICE.TechnicSheetService.get_object(id=technic_sheet_id)
#     ts.driver_sheet = ds
#     ts.save(update_fields=['driver_sheet'])
#     log.info("The driver has been changed for technic_sheet")
#     if ds:
#         return ds.status
#     else:
#         return None

# def autocomplete_driver_from_technic_sheet(workday_instance: WorkDaySheet):
#     """
#     Авто подстановка закрепленного водителя
#     :param workday_instance:
#     :return:
#     """
#     empty_technic_sheet = (
#         TECHNIC_SHEET_SERVICE
#         .TechnicSheetService
#         .get_queryset(
#             date=workday_instance,
#             isArchive=False,
#             driver_sheet__isnull=True,
#             technic__attached_driver__isnull=False
#             )
#         .select_related('driver_sheet', 'technic__attached_driver'))
#
#     if empty_technic_sheet.exists():
#         log.info("empty_technic_sheet.exists() is True")
#         driver_sheet_list = DRIVER_SHEET_SERVICE.DriverSheetService.get_queryset(
#             isArchive=False,
#             status=True,
#             date=workday_instance
#         ).select_related('driver')
#
#         for e_ts in empty_technic_sheet:
#             _ts = TECHNIC_SHEET_SERVICE.TechnicSheetService.get_queryset(
#                 date=workday_instance,
#                 driver_sheet__driver=e_ts.technic.attached_driver
#             ).select_related('driver_sheet__driver', 'technic__attached_driver')
#             _ds = driver_sheet_list.filter(driver=e_ts.technic.attached_driver)
#             if _ts.count() == 0:
#                 e_ts.driver_sheet = _ds.first()
#                 e_ts.save(update_fields=['driver_sheet'])
#     else:
#         log.info("empty_technic_sheet.exists() is False")

# def calculate_count_app_for_technic_sheet(technic_sheet_id, exclude_app_tech_list: list = None) -> int:
#     ts = TECHNIC_SHEET_SERVICE.TechnicSheetService.get_object(id=technic_sheet_id)
#     app_tech = APP_TECHNIC_SERVICE.get_apps_technic_queryset(   #TODO: ref
#         technic_sheet=ts,
#         isChecked=False,
#         isArchive=False,
#         is_cancelled=False
#     )
#     if exclude_app_tech_list:
#         count_app_tech = app_tech.exclude(application_today__id=exclude_app_tech_list).count()
#     else:
#         count_app_tech = app_tech.count()
#     ts.count_application = count_app_tech
#     ts.save(update_fields=['count_application'])
#     return count_app_tech

# def calculate_all_app_for_technic_sheet(ids_list: list[int], **kwargs):
#     ts_list = TECHNIC_SHEET_SERVICE.TechnicSheetService.get_queryset(
#         id__in=ids_list,
#         isArchive=False
#     )
#     for ts in ts_list:
#         calculate_count_app_for_technic_sheet(technic_sheet_id=ts.id, **kwargs)

# def get_ids_list_from_model(model: models.Model | QuerySet[models.Model]) -> list[int]:
#     if isinstance(model, models.Model):
#         return [model.pk]
#     elif isinstance(model, QuerySet):
#         return list(model.values_list('id', flat=True))
#     else:
#         return []


# def get_busiest_technic_title(technic_sheet: QuerySet[TechnicSheet]) -> list:
#     """
#     Получения списка с информацией о загруженности technic_title
#     :param technic_sheet:
#     :return: [{}, {}]
#     """
#     out = []
#     technic_sheet = technic_sheet.exclude(
#         applicationtechnic__application_today__status=ASSETS.ApplicationTodayStatus.SAVED.title
#     )
#     technic_title_list = TECHNIC_SERVICE.get_distinct_technic_title(technic_sheet)
#
#     for technic_title in technic_title_list:
#         technic__title = technic_sheet.filter(technic__title=technic_title, driver_sheet__status=True)
#         technic__title_list = technic__title.values('id', 'count_application')
#         total_technic_sheet_count = technic__title_list.count()
#         all_applications_count = sum(technic__title.values_list('count_application', flat=True))
#         need_technics_count = all_applications_count - total_technic_sheet_count
#
#         out.append({
#             'technic_title': technic_title,
#             'free_technic_sheet_count': technic__title_list.filter(count_application=0).count(),
#             'total_technic_sheet_count': total_technic_sheet_count,
#             'id_list': list(technic__title_list.values_list('id', flat=True)),
#             'all_applications_count': all_applications_count,
#             'need_technics_count': need_technics_count
#         })
#     return out


# def get_conflict_list_of_technic_sheet(busiest_technic_title: list, priority_id_list: set,
#                                        get_only_id_list=False) -> list:
#     """
#     Получить список конфликтов technic_sheet
#     :param busiest_technic_title: список с информацией о загруженности technic_title
#     :param priority_id_list: сет technic_sheet_id с нераспределенным приоритетом
#     :param get_only_id_list: True - получить только id; False - получить более подробную информацию
#     :return: [{}, {}, ...]
#     """
#     out = []
#     for _technic_sheet in busiest_technic_title:
#         if _technic_sheet['need_technics_count'] > 0 and set(_technic_sheet['id_list']).intersection(priority_id_list):
#             if get_only_id_list:
#                 out.extend(_technic_sheet['id_list'])
#             else:
#                 out.append(_technic_sheet)
#     return out


# def get_priority_id_list(technic_sheet: QuerySet[TechnicSheet]) -> set:
#     """
#     Получения сета technic_sheet_id с нераспределенным приоритетом
#     :param technic_sheet:
#     :return: set(.., ...)
#     """
#     technic_sheet = technic_sheet.exclude(
#         applicationtechnic__application_today__status=ASSETS.ApplicationTodayStatus.SAVED.title,
#
#     )
#     technic_sheet_list_id_list = technic_sheet.filter(count_application__gt=0, driver_sheet__status=True).values('id')
#     application_technic_list = tuple(APP_TECHNIC_SERVICE.get_apps_technic_queryset(
#         technic_sheet__in=technic_sheet_list_id_list,
#         isArchive=False,
#         is_cancelled=False,
#         isChecked=False
#     ).values(
#         'technic_sheet__id',
#         'priority'
#     ))
#     out = {item['technic_sheet__id'] for item in application_technic_list if application_technic_list.count(item) > 1}
#     return out


# def set_color_for_list(some_list: list) -> dict:
#     """
#     Привязка цвета для каждого элемента из списка some_list
#     :param some_list:
#     :return:
#     """
#     colors = ASSETS.COLORS[:]
#     random.shuffle(colors)
#     out = {int(id_): color for id_, color in zip(some_list, colors)}
#     return out


# def sorting_application_status(item):
#     """
#     Сортировка application_today по статусу
#     :param item:
#     :return:
#     """
#     if item is None or item['application_today'] is None:
#         return 10
#
#     status = item['application_today']['status']
#
#     if status == ASSETS.ApplicationTodayStatus.SAVED.title:
#         return 1
#     if status == ASSETS.ApplicationTodayStatus.SUBMITTED.title:
#         return 5
#     if status == ASSETS.ApplicationTodayStatus.APPROVED.title:
#         return 5
#     if status == ASSETS.ApplicationTodayStatus.SEND.title:
#         return 5
#     if status == ASSETS.ApplicationTodayStatus.DELETED.title:
#         return 7
#     if status == ASSETS.ApplicationTodayStatus.ABSENT.title:
#         return 9


# def accept_app_tech_to_supply(app_tech_id, application_today_id):
#     """
#     Принять заявку ApplicationTechnic(id=app_tech_id) для supply
#     :param app_tech_id:
#     :param application_today_id:
#     :return:
#     """
#     application_technic = APP_TECHNIC_SERVICE.get_app_technic(pk=app_tech_id)
#     application_today = APP_TODAY_SERVICE.get_apps_today(pk=application_today_id)
#     if all((application_technic, application_today)):
#
#         if application_technic.is_cancelled:
#             application_technic.is_cancelled = False
#             application_technic.description = application_technic.description.replace(
#                 ASSETS.MessagesAssets.reject.value, "")
#             application_technic.technic_sheet.increment_count_application()
#             application_technic.technic_sheet.save()
#             application_technic.save()
#
#         cs_address = application_technic.application_today.construction_site.address
#         cs_foreman = application_technic.application_today.construction_site.foreman
#         cs_foreman__last_name = cs_foreman.last_name if cs_foreman is not None else None
#
#         str_constr_site = f"> {cs_address} {'('+cs_foreman__last_name+')' if cs_foreman__last_name else ''}:\n".upper()
#         str_desc = str_constr_site + application_technic.description + '\n'
#
#         if not application_technic.isChecked:
#             _new_app_tech, created = ApplicationTechnic.objects.get_or_create(
#                 technic_sheet=application_technic.technic_sheet,
#                 application_today=application_today
#             )
#             _new_app_tech.description = _new_app_tech.description + str_desc if _new_app_tech.description else str_desc
#             _new_app_tech.save()
#
#             application_technic.isChecked = True
#             application_technic.id_orig_app = _new_app_tech.id
#             application_technic.save()
#             TECHNIC_SHEET_SERVICE.calculate_count_applications(application_technic.technic_sheet_id)
#
#         elif application_technic.isChecked:
#             _supply_at = APP_TECHNIC_SERVICE.get_app_technic(
#                 pk=application_technic.id_orig_app
#             )
#             _supply_at.description = _supply_at.description.replace(str_desc, '')
#             _supply_at.save()
#             if not _supply_at.description:
#                 _supply_at.delete()
#             application_technic.isChecked = False
#
#             application_technic.id_orig_app = None
#             application_technic.save()
#             TECHNIC_SHEET_SERVICE.calculate_count_applications(application_technic.technic_sheet_id)


# def get_table_working_technic_sheet(current_day: WorkDaySheet):
#     """
#     Получить таблицу загруженность для dashboard
#     :param current_day:
#     :return:
#     """
#     _technic_sheet = TECHNIC_SHEET_SERVICE.get_technic_sheet_queryset(
#         select_related=('driver_sheet__driver', 'technic__attached_driver'),
#         isArchive=False,
#         date=current_day
#     )
#     return _technic_sheet.order_by('driver_sheet__driver__last_name')


# def change_view_props(io_name: str, io_status: str, io_value: str, user: User) -> bool:
#     if io_status == 'true':
#         status = True
#     elif io_status == 'false':
#         status = False
#     else:
#         status = None
#
#     if status is not None:
#         match io_name:
#             case 'is_show_deleted_app':
#                 user.is_show_deleted_app = status
#                 user.save(update_fields=['is_show_deleted_app'])
#                 return True
#             case 'is_show_saved_app':
#                 user.is_show_saved_app = status
#                 user.save(update_fields=['is_show_saved_app'])
#                 return True
#             case 'is_show_absent_app':
#                 user.is_show_absent_app = status
#                 user.save(update_fields=['is_show_absent_app'])
#                 return True
#             case 'is_show_technic_app':
#                 user.is_show_technic_app = status
#                 user.save(update_fields=['is_show_technic_app'])
#                 return True
#             case 'is_show_material_app':
#                 user.is_show_material_app = status
#                 user.save(update_fields=['is_show_material_app'])
#                 return True
#             case 'io_color_title':
#                 color = io_value if io_value is not None else '#000000'
#                 user.color_title = color
#                 user.save(update_fields=['color_title'])
#                 return True
#             case 'io_font_size':
#                 if io_value == '' or io_value is None:
#                     font_size = 10
#                 else:
#                     try:
#                         font_size = int(io_value)
#                     except Exception as e:
#                         log.error(f"set_data_for_filter(): 'font_size' | {e}")
#                         font_size = 10
#                 user.font_size = font_size
#                 user.save(update_fields=['font_size'])
#                 return True
#
#             case _:
#                 return False


# def set_data_for_filter(request):
#     """
#     Установка параметров фильтрации
#     :param request:
#     :return:
#     """
#
#     filter_construction_site = request.POST.get('filter_construction_site')
#     filter_construction_site = filter_construction_site if filter_construction_site is not None else 0
#
#     filter_foreman = request.POST.get('filter_foreman')
#     filter_foreman = filter_foreman if filter_foreman is not None else 0
#
#     filter_technic = request.POST.get('filter_technic')
#     filter_technic = filter_technic if filter_technic != '' else None
#
#     sort_by = request.POST.get('sort_by')
#     sort_by = sort_by if sort_by != '' else None
#
#     _user = USERS_SERVICE.get_user(pk=request.user.id)
#     if _user:
#
#         if filter_construction_site is not None:
#             _user.filter_construction_site = filter_construction_site
#         if filter_foreman is not None:
#             _user.filter_foreman = filter_foreman
#
#         _user.filter_technic = filter_technic
#         _user.sort_by = sort_by
#         _user.save()


# def prepare_data_for_filter(context: dict) -> dict:
#     """
#     Подготовка и получения данных для фильтра
#     :param context:
#     :return:
#     """
#     foreman_list = USERS_SERVICE.get_user_queryset(post=ASSETS.UserPosts.FOREMAN.title)
#     construction_site_list = CONSTR_SITE_SERVICE.get_construction_site_queryset(
#         status=True,
#         isArchive=False,
#         select_related=('foreman',),
#         order_by=('address',)
#     )
#
#     technic_list = TECHNIC_SERVICE.TechnicService.get_technics_queryset(
#         isArchive=False
#     ).values_list('title', flat=True).distinct()
#
#     sort_by_list = ASSETS.SORT_BY
#
#     context['filter_foreman_list'] = foreman_list
#     context['filter_construction_site_list'] = construction_site_list
#     context['filter_technic_list'] = technic_list
#     context['sort_by_list'] = sort_by_list
#     return context


# def send_messages_by_telegram(chat_id, messages):
#     """
#     Отправка messages пользователю с chat_id через Telegram
#     :param chat_id:
#     :param messages:
#     :return:
#     """
#     if USE_TELEGRAM:
#         try:
#             T.BOT.send_message(chat_id=chat_id, text=messages, parse_mode='html')
#         except T.ApiTelegramException as e:
#             log.error('send_messages_by_telegram(): ApiTelegramException [%s]' % chat_id)


# def get_user_key(user_id) -> str:
#     """
#     Получить уникальный ключ для привязки Telegram
#     :param user_id:
#     :return:
#     """
#     _user = USERS_SERVICE.get_user(pk=user_id)
#     if _user:
#         _key = random.randint(100, 999)
#         return f'{_key}{_user.id}'


# def send_application_by_telegram_for_driver(current_day: WorkDaySheet, messages=None, application_today_id=None):
#     all_already_send = current_day.is_all_application_send
#     template_date = f'{ASSETS.WEEKDAY[current_day.date.weekday()]}, {current_day.date.day} {ASSETS.MONTHS_T[current_day.date.month - 1]}'
#     driver_list = TECHNIC_SHEET_SERVICE.get_technic_sheet_queryset(
#         date=current_day,
#         status=True,
#         driver_sheet__status=True,
#         isArchive=False
#     )
#     if application_today_id:
#         application_today = APP_TODAY_SERVICE.get_apps_today_queryset(pk=application_today_id)
#     else:
#         application_today = APP_TODAY_SERVICE.get_apps_today_queryset(
#             isArchive=False,
#             date=current_day,
#             status=ASSETS.ApplicationTodayStatus.SEND.title)
#
#     application_technic_list = APP_TECHNIC_SERVICE.get_apps_technic_queryset(
#         select_related=('technic_sheet', 'application_today__construction_site__foreman'),
#         isArchive=False,
#         is_cancelled=False,
#         isChecked=False,
#         application_today__in=application_today
#     )
#
#     driver_sheet_list = driver_list.filter(
#         id__in=application_technic_list.values_list('technic_sheet_id', flat=True)).values(
#         'id',
#         'driver_sheet__driver__telegram_id_chat',
#         'driver_sheet__driver__last_name',
#         'driver_sheet__driver__first_name',
#     )
#
#     for driver_sheet_item in driver_sheet_list:
#         driver_sheet_item['applications'] = application_technic_list.filter(
#             technic_sheet_id=driver_sheet_item['id']).values(
#             'priority',
#             'application_today__construction_site__address',
#             'application_today__construction_site__foreman__last_name',
#             'application_today__is_application_send',
#             'description'
#         ).order_by('priority')
#
#     if all_already_send:
#         msg = f'Обновленная заявка на:\n{template_date}\n\n'
#     else:
#         msg = f'Заявка на:\n{template_date}\n\n'
#
#     for item in driver_sheet_list:
#         msg = ''
#         msg = f"{item['driver_sheet__driver__last_name']} {item['driver_sheet__driver__first_name']}\n{msg}"
#         for app in item['applications']:
#             if app['application_today__construction_site__foreman__last_name']:
#                 msg += f"{app['priority']}) {app['application_today__construction_site__address']} ({app['application_today__construction_site__foreman__last_name']})\n"
#             else:
#                 msg += f"{app['priority']}) {app['application_today__construction_site__address']}\n"
#             if app['description']:
#                 msg += f"{app['description']}\n\n"
#             else:
#                 msg += f"\n"
#         if item['driver_sheet__driver__telegram_id_chat']:
#             send_messages_by_telegram(chat_id=item['driver_sheet__driver__telegram_id_chat'], messages=msg)


# def send_application_by_telegram_for_foreman(current_day: WorkDaySheet, messages=None, application_today_id=None):
#     all_already_send = current_day.is_all_application_send
#     template_date = f'{ASSETS.WEEKDAY[current_day.date.weekday()]}, {current_day.date.day} {ASSETS.MONTHS_T[current_day.date.month - 1]}'
#     foreman_list = USERS_SERVICE.get_user_queryset(
#         isArchive=False,
#         post__in=(ASSETS.UserPosts.FOREMAN.title, ASSETS.UserPosts.MASTER.title, ASSETS.UserPosts.SUPPLY.title)
#     ).values(
#         'id',
#         'last_name',
#         'first_name',
#         'post',
#         'supervisor_user_id',
#         'telegram_id_chat'
#     )
#
#     if application_today_id:
#         application_today = APP_TODAY_SERVICE.get_apps_today_queryset(
#             select_related=('construction_site__foreman',),
#             pk=application_today_id)
#     else:
#         application_today = APP_TODAY_SERVICE.get_apps_today_queryset(
#             select_related=('construction_site__foreman',),
#             isArchive=False, date=current_day, status=ASSETS.ApplicationTodayStatus.SEND.title)
#
#     for item in foreman_list:
#         if item['post'] == ASSETS.UserPosts.FOREMAN.title:
#             foreman_id = item['id']
#         else:
#             foreman_id = item['supervisor_user_id']
#         if foreman_id:
#             app_today = application_today.filter(construction_site__foreman_id=foreman_id)
#         else:
#             app_today = application_today.filter(construction_site__address=ASSETS.MessagesAssets.CS_SUPPLY_TITLE.value)
#         item['applications'] = app_today.values(
#             'construction_site__address',
#             'is_application_send'
#         )
#
#     for item in foreman_list:
#         if all_already_send:
#             msg = f"Повторное уведомление:\n{template_date}\n"
#         else:
#             msg = f"{template_date}\n"
#         if item['applications']:
#             for app in item['applications']:
#                 if app['is_application_send']:
#                     msg = f"Повторное уведомление:\n{template_date}\n"
#                 else:
#                     msg = msg
#                 msg += f"Заявка на {app['construction_site__address']} одобрена\n"
#             if item['telegram_id_chat']:
#                 send_messages_by_telegram(chat_id=item['telegram_id_chat'], messages=msg)


# def send_application_by_telegram_for_admin(current_day: WorkDaySheet, messages=None, application_today_id=None):
#     template_date = f'{ASSETS.WEEKDAY[current_day.date.weekday()]}, {current_day.date.day} {ASSETS.MONTHS_T[current_day.date.month - 1]}'
#     administrators_list = USERS_SERVICE.get_user_queryset(isArchive=False, post=ASSETS.UserPosts.ADMINISTRATOR.title)
#
#     if current_day.is_all_application_send:
#         msg = f"Заявки на:\n{template_date} отправлены повторно"
#     else:
#         msg = f"Заявки на:\n{template_date} отправлены"
#
#     if application_today_id:
#         app_today = APP_TODAY_SERVICE.get_apps_today(pk=application_today_id)
#         if app_today:
#             if app_today.construction_site.foreman:
#                 msg_constr_site = f'{app_today.construction_site.address} ({app_today.construction_site.foreman})'
#             else:
#                 msg_constr_site = f'{app_today.construction_site.address}'
#
#             if app_today.is_application_send:
#                 msg = f"Заявка на:\n{template_date}\nобъект: {msg_constr_site} отправлена повторно"
#             else:
#                 msg = f"Заявка на:\n{template_date}\nобъект: {msg_constr_site} отправлена"
#
#     messages = messages if messages else msg
#
#     [send_messages_by_telegram(admin.telegram_id_chat, messages)
#      for admin in administrators_list if admin.telegram_id_chat]


# def send_application_by_telegram_for_all(current_day: WorkDaySheet, messages=None, application_today_id=None):
#     """
#     Отправка заявок всем пользователям через Telegram
#     :param current_day:
#     :param messages:
#     :param application_today_id:
#     :return:
#     """
#     send_application_by_telegram_for_driver(current_day, messages, application_today_id)
#     send_application_by_telegram_for_foreman(current_day, messages, application_today_id)
#     send_application_by_telegram_for_admin(current_day, messages, application_today_id)
#     if application_today_id:
#         APP_TODAY_SERVICE.get_apps_today(pk=application_today_id).send_application()
#     else:
#         current_day.send_all_application()


# def copy_application_to_target_day(id_application_today,
#                                    _target_day: date,
#                                    default_status: str = ASSETS.ApplicationTodayStatus.SAVED.title):
#     """
#     Копирование заявки ApplicationToday(id=id_application_today) на _target_day
#     :param id_application_today:
#     :param _target_day:
#     :param default_status: saved | submitted
#     :return:
#     """
#     target_day = WORK_DAY_SERVICE.get_workday(_target_day)
#     current_application = APP_TODAY_SERVICE.get_apps_today(pk=id_application_today)
#
#     new_application, _ = ApplicationToday.objects.get_or_create(
#         date=target_day, status=default_status, description=current_application.description,
#         construction_site=current_application.construction_site)
#
#     current_application_material = APP_MATERIAL_SERVICE.get_apps_material_queryset(
#         application_today=current_application)
#     if current_application_material.exists():
#         new_application_material, _ = ApplicationMaterial.objects.get_or_create(application_today=new_application)
#         new_application_material.description = current_application_material.first().description
#         new_application_material.save()
#
#     current_application_technic = APP_TECHNIC_SERVICE.get_apps_technic_queryset(
#         select_related=('technic_sheet__technic',),
#         application_today=current_application)
#
#     for tech_app in current_application_technic:
#         if tech_app.technic_sheet:
#             target_technic_sheet = TECHNIC_SHEET_SERVICE.get_technic_sheet(
#                 date=target_day,
#                 status=True,
#                 isArchive=False,
#                 technic=tech_app.technic_sheet.technic)
#
#             if target_technic_sheet:
#                 new_app_tech, _ = ApplicationTechnic.objects.get_or_create(
#                     application_today=new_application,
#                     technic_sheet=target_technic_sheet)
#                 new_app_tech.description = tech_app.description
#                 new_app_tech.save()
#                 target_technic_sheet.increment_count_application()


# def set_spec_task(technic_sheet_id):
#     """
#     Отправить technic_sheet в спец. объект и назначить спец. задание по умолчанию
#     :param technic_sheet_id:
#     :return:
#     """
#     construction_site, _ = ConstructionSite.objects.get_or_create(address=ASSETS.MessagesAssets.CS_SPEC_TITLE.value)
#
#     technic_sheet = TECHNIC_SHEET_SERVICE.get_technic_sheet(pk=technic_sheet_id)
#     current_day = technic_sheet.date
#     application_today, _ = ApplicationToday.objects.get_or_create(
#         construction_site=construction_site,
#         date=current_day)
#
#     application_technic, at_created = ApplicationTechnic.objects.get_or_create(
#         application_today=application_today,
#         technic_sheet=technic_sheet)
#     if at_created:
#         technic_sheet.increment_count_application()
#
#     template_description = TECHNIC_SERVICE.get_description_mode_for_spec_app(technic_sheet.technic.id)
#     match template_description:
#         case ASSETS.TaskDescriptionMode.DEFAULT:
#             description = PARAMETER_SERVICE.get_parameter(
#                 name=VAR.VAR_TASK_DESCRIPTION_FOR_SPEC_CONSTR_SITE['name']
#             ).value
#         case ASSETS.TaskDescriptionMode.MANUAL:
#             description = TECHNIC_SERVICE.get_task_description(
#                 technic__id=technic_sheet.technic.id).description
#         case ASSETS.TaskDescriptionMode.AUTO:
#             prev_workday = WORK_DAY_SERVICE.get_prev_workday(current_day.date)
#             task_description = APP_TECHNIC_SERVICE.get_apps_technic_queryset(
#                 application_today__construction_site__address=ASSETS.MessagesAssets.CS_SPEC_TITLE.value,
#                 application_today__date=prev_workday,
#                 technic_sheet__technic=technic_sheet.technic,
#             )
#             if task_description.exists():
#                 description = task_description.first().description
#             else:
#                 description = ''
#         case _:
#             description = ''
#
#     application_technic.description = description
#     application_technic.save()
#     application_today.status = ASSETS.ApplicationTodayStatus.SUBMITTED.title
#     application_today.save(update_fields=['status'])


# def get_view_mode(_date: date) -> str:
#     """
#     Получить режим отображения
#     :param _date:
#     :return:
#     """
#     if _date == TODAY:
#         return ASSETS.ViewMode.CURRENT.value
#     elif _date < TODAY:
#         return ASSETS.ViewMode.ARCHIVE.value
#     elif _date > TODAY:
#         return ASSETS.ViewMode.FUTURE.value
#     else:
#         return 'None'


# def get_accept_mode_by_date(workday: WorkDaySchema) -> bool:
#     """
#     Получить режим accept mode
#     True - заявки принимаются
#     False - заявки не принимаются
#     :param workday:
#     :return:
#     """
#
#     var_time_recept_apps = PARAMETER_SERVICE.ParameterService.get_object(
#         name=VAR.VAR_TIME_RECEPTION_OF_TECHNICS['name']
#     )
#     if var_time_recept_apps:
#         if workday.accept_mode == ASSETS.AcceptMode.AUTO.value:
#             if var_time_recept_apps.time < datetime.now().time():
#                 return True
#             else:
#                 return False
#         elif workday.accept_mode == ASSETS.AcceptMode.MANUAL.value:
#             return True
#         elif workday.accept_mode == ASSETS.AcceptMode.OFF.value:
#             return False


# def get_accept_mode(accept_mode: str) -> Literal[AcceptMode.AUTO, AcceptMode.MANUAL, AcceptMode.OFF] | None:
#     """ Получить режим accept mode"""
#     if accept_mode == ASSETS.AcceptMode.AUTO.value:
#         return ASSETS.AcceptMode.AUTO
#     elif accept_mode == ASSETS.AcceptMode.MANUAL.value:
#         return ASSETS.AcceptMode.MANUAL
#     elif accept_mode == ASSETS.AcceptMode.OFF.value:
#         return ASSETS.AcceptMode.OFF


# def set_accept_mode(current_day: WorkDaySheet, mode: ASSETS.AcceptMode):
#     """
#     Установить режим accept mode
#     :param current_day:
#     :param mode:
#     :return:
#     """
#     current_day.accept_mode = mode.value
#     current_day.save(update_fields=['accept_mode'])


# def is_valid_get_request(value: str) -> bool:
#     """
#     Проверка : value is not None and value != ''
#     :param value:
#     :return:
#     """
#     if value is not None and value != '':
#         return True
#     else:
#         return False


# def change_up_status_for_application_today(workday: WorkDaySheet, application_today_id=None,
#                                            current_status=None) -> str:
#     """
#     Изменить статус заявки на следующий статус
#     :param workday:
#     :param application_today_id:
#     :param current_status:
#     :return:
#     """
#     if application_today_id:
#         application_today = APP_TODAY_SERVICE.get_apps_today(pk=application_today_id)
#         application_today.set_next_status()
#         return application_today.status
#     else:
#         application_today_list = APP_TODAY_SERVICE.get_apps_today_queryset(
#             isArchive=False,
#             date=workday,
#             status=current_status
#         )
#         [application_today.set_next_status() for application_today in application_today_list]
#         if application_today_list.exists():
#             return application_today_list.first().status
#         else:
#             return current_status


# def get_status_lists_of_apps_today(applications_today: QuerySet[ApplicationToday]) -> dict:
#     """
#     Получить сгруппированный по статусам dict с id объектами ApplicationToday
#     :param applications_today:
#     :return: {absent: [], saved: [], submitted: [], approved: [], send: []}
#     """
#     status_lists: dict[str, list] = {
#         ASSETS.ApplicationTodayStatus.ABSENT.title: [],
#         ASSETS.ApplicationTodayStatus.SAVED.title: [],
#         ASSETS.ApplicationTodayStatus.SUBMITTED.title: [],
#         ASSETS.ApplicationTodayStatus.APPROVED.title: [],
#         ASSETS.ApplicationTodayStatus.SEND.title: []
#     }
#
#     apps_today = applications_today.values('id', 'status')
#     for app in apps_today:
#         if app['status'] == ASSETS.ApplicationTodayStatus.ABSENT.title:
#             status_lists[ASSETS.ApplicationTodayStatus.ABSENT.title].append(app['id'])
#         elif app['status'] == ASSETS.ApplicationTodayStatus.SAVED.title:
#             status_lists[ASSETS.ApplicationTodayStatus.SAVED.title].append(app['id'])
#         elif app['status'] == ASSETS.ApplicationTodayStatus.SUBMITTED.title:
#             status_lists[ASSETS.ApplicationTodayStatus.SUBMITTED.title].append(app['id'])
#         elif app['status'] == ASSETS.ApplicationTodayStatus.APPROVED.title:
#             status_lists[ASSETS.ApplicationTodayStatus.APPROVED.title].append(app['id'])
#         elif app['status'] == ASSETS.ApplicationTodayStatus.SEND.title:
#             status_lists[ASSETS.ApplicationTodayStatus.SEND.title].append(app['id'])
#     return status_lists


# def prepare_global_parameters():
#     """
#     Авто создание переменных
#     :return:
#     """
#     parameters_list = VAR.VARIABLES_LIST
#     # PARAMETER_SERVICE.create_global_parameters(global_parameters=parameters_list)
#     PARAMETER_SERVICE.ParameterService.auto_create_global_parameters(global_parameters=parameters_list)


# def get_accept_to_change_materials_app(current_workday: WorkDaySheet) -> bool:
#     """
#     Разрешено ли редактировать заявки на материалы
#     :param current_workday:
#     :return:
#     """
#     is_accept = False
#     var_time_limit = PARAMETER_SERVICE.get_parameter(
#         name=VAR.VAR_TIME_RECEPTION_OF_MATERIALS['name']
#     )
#     if not var_time_limit:
#         log.warning(
#             f"Variable {VAR.VAR_TIME_RECEPTION_OF_MATERIALS['name']} \
#             There is no time limit for submitting applications for materials.")
#         return False
#
#     time_limit = var_time_limit.time
#     next_workday = WORK_DAY_SERVICE.get_next_workday()
#
#     if (current_workday == next_workday
#             and NOW() < time_limit):
#         is_accept = True
#         log.debug("get_accept_to_change_materials_app(): C1")
#
#     elif TODAY.weekday() in (4,) and current_workday.date.weekday() in (0,) and NOW() < time_limit:
#         is_accept = True
#         log.debug("get_accept_to_change_materials_app(): C2")
#
#     elif current_workday.date > next_workday.date:
#         is_accept = True
#         log.debug("get_accept_to_change_materials_app(): C3")
#
#     return is_accept


# def validate_telephone(telephone: str, length=9, use_pref=True) -> str | None:
#     """
#     Валидация номера телефона
#     :param use_pref:
#     :param length:
#     :param telephone:
#     :return:
#     """
#     if telephone:
#         pref = '+375'
#         out = [sym for sym in telephone if sym in '0123456789']
#         out = ''.join(out)
#
#         if len(out) >= length:
#             if use_pref:
#                 return pref + out[-length:]
#             else:
#                 return out[-length:]
#         else:
#             return None
#     return None


# def is_redirect_to_dashboard(request_meta: dict) -> bool:
#     """
#     Перенаправить ли на главную страницу
#     :param request_meta:
#     :return: True | False
#     """
#     if request_meta.get('HTTP_REFERER') is None:
#         return True
#     else:
#         return False


# def validate_post(post: str) -> bool:
#     """
#     Валидация должности пользователя
#     :param post:
#     :return:
#     """
#     return True if post in ASSETS.UserPosts.get_set() else False
#
# #   ================================================================


# def delete_user(user_id: int):
#     """
#     Удаление пользователя
#     :param user_id:
#     :return:
#     """
#     user = USERS_SERVICE.delete_user(id=user_id)
#     if user:
#         DRIVER_SHEET_SERVICE.get_driver_sheet_queryset(driver=user.id, date__date__gte=TODAY).delete()


# def delete_technic(technic_id: int):
#     """
#     Удаление техники
#     :param technic_id:
#     :return:
#     """
#     # technic = TECHNIC_SERVICE.delete_technic(technic_id)
#     technic = TECHNIC_SERVICE.TechnicService.delete(id=technic_id)
#     if technic:
#         _technic_sheet = TECHNIC_SHEET_SERVICE.get_technic_sheet_queryset(
#             technic=technic,
#             date__date__gte=TODAY
#         )
#         _application_technic = APP_TECHNIC_SERVICE.get_apps_technic_queryset(
#             technic_sheet__in=_technic_sheet
#         )
#         _application_today = APP_TODAY_SERVICE.get_apps_today_queryset(
#             date__date__gte=TODAY
#         )
#
#         _application_technic.delete()
#         _technic_sheet.delete()
#
#         for _app_today in _application_today:
#             # APP_TODAY_SERVICE.validate_application_today(application_today=_app_today)
#             validate_application_today(application_today=_app_today)


# def delete_application_today(application_today_id: int):
#     """
#     Удалить application_today: ApplicationToday и деинкрементировать technic_sheet
#     :param application_today_id:
#     :return:
#     """
#     technic_sheet_id_list = APP_TECHNIC_SERVICE.ApplicationTechnicService.get_queryset(
#         isArchive=False,
#         application_today_id=application_today_id
#     ).values_list('technic_sheet', flat=True)
#
#     calculate_all_app_for_technic_sheet(
#         list(technic_sheet_id_list),
#         exclude_app_tech_list=application_today_id
#     )
#     APP_TODAY_SERVICE.ApplicationTodayService.delete(id=application_today_id)

# def restore_application_today(
#         application_today_id: int,
#         status: Literal["deleted", "absent", "saved", "submitted", "approved", "send"]
# ):
#     """
#     Восстановить application_today: ApplicationToday и деинкрементировать technic_sheet
#     :param application_today_id:
#     :param status:
#     :return:
#     """
#     technic_sheet_id_list = APP_TECHNIC_SERVICE.ApplicationTechnicService.get_queryset(
#         isArchive=False,
#         application_today_id=application_today_id
#     ).values_list('technic_sheet', flat=True)
#     calculate_all_app_for_technic_sheet(list(technic_sheet_id_list))
#     APP_TODAY_SERVICE.ApplicationTodayService.restore(status=status, id=application_today_id)

# def get_default_status_for_apps_today(
#         current_user: USERS_SERVICE.UserSchema
# ) -> Literal["deleted", "absent", "saved", "submitted", "approved", "send"]:
#     if is_admin(current_user):
#         return ASSETS.ApplicationTodayStatus.SUBMITTED.title
#     elif is_mechanic(current_user):
#         return ASSETS.ApplicationTodayStatus.SUBMITTED.title
#     else:
#         return ASSETS.ApplicationTodayStatus.SAVED.title

# def validate_application_today(
#         application_today: ApplicationToday,
#         default_status: Literal["deleted", "absent", "saved", "submitted", "approved", "send"] | None = None
# ) -> bool:
#     """
#     Проверка application_today: ApplicationToday
#     :param application_today: application_today: ApplicationToday
#     :param default_status: save or submitted
#     :return: True if application_today is valid and save, else False and delete
#     """
#     app_today_description: bool = application_today.description is not None and application_today.description != ''
#
#     app_technic__is_exist = APP_TECHNIC_SERVICE.ApplicationTechnicService.is_exist(
#         application_today=application_today,
#         isArchive=False,
#     )
#     app_material__is_exist = APP_MATERIAL_SERVICE.ApplicationMaterialService.is_exist(
#         application_today=application_today,
#         isArchive=False,
#     )
#
#     if any((app_today_description, app_technic__is_exist, app_material__is_exist)):
#         if application_today.is_edited and default_status:
#             application_today.status = default_status
#             application_today.is_edited = False
#         application_today.save()
#         return True
#     else:
#         application_today.delete()
#         return False


# def validate_cache_name(raw_name: str) -> str:
#     return raw_name.strip().replace(" ",'')
#
#
# def is_admin(current_user: USERS_SERVICE.UserSchema) -> bool:
#     return ASSETS.UserPosts.ADMINISTRATOR.title == current_user.post
#
# def is_foreman(current_user: USERS_SERVICE.UserSchema) -> bool:
#     return ASSETS.UserPosts.FOREMAN.title == current_user.post
#
# def is_master(current_user: USERS_SERVICE.UserSchema) -> bool:
#     return ASSETS.UserPosts.MASTER.title == current_user.post
#
# def is_driver(current_user: USERS_SERVICE.UserSchema) -> bool:
#     return ASSETS.UserPosts.DRIVER.title == current_user.post
#
# def is_mechanic(current_user: USERS_SERVICE.UserSchema) -> bool:
#     return ASSETS.UserPosts.MECHANIC.title == current_user.post
#
# def is_supply(current_user: USERS_SERVICE.UserSchema) -> bool:
#     return ASSETS.UserPosts.SUPPLY.title == current_user.post
#
# def is_employee(current_user: USERS_SERVICE.UserSchema) -> bool:
#     return ASSETS.UserPosts.EMPLOYEE.title == current_user.post

