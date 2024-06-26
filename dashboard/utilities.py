from dashboard.models import WorkDaySheet, DriverSheet, TechnicSheet, ConstructionSite, ApplicationMaterial
from django.db.models.query import QuerySet
from django.db.models import Q
from dashboard.models import ApplicationToday, ApplicationTechnic
from dashboard.models import Technic
# from dashboard.models import Administrator, Foreman, Master, Mechanic, Driver, Supply, Employee
from dashboard.models import User
from dashboard.models import Parameter

#   ------------------------------------------------------------------------------------------------------------------


from datetime import date, timedelta, datetime
import random
from functools import cmp_to_key

import dashboard.assets as ASSETS
import dashboard.telegram_bot as T
import dashboard.variables as VAR

#   ------------------------------------------------------------------------------------------------------------------

TODAY = date.today()
NOW = datetime.now().time()


def is_administrator(user: User) -> bool:
    return True if user.post == ASSETS.ADMINISTRATOR else False


def is_foreman(user: User) -> bool:
    return True if user.post == ASSETS.FOREMAN else False


def is_master(user: User) -> bool:
    return True if user.post == ASSETS.MASTER else False


def is_driver(user: User) -> bool:
    return True if user.post == ASSETS.DRIVER else False


def is_mechanic(user: User) -> bool:
    return True if user.post == ASSETS.MECHANIC else False


def is_supply(user: User) -> bool:
    return True if user.post == ASSETS.SUPPLY else False


def is_employee(user: User) -> bool:
    return True if user.post == ASSETS.EMPLOYEE else False


def convert_str_to_date(str_date: str) -> date:
    """конвертация str в datetime.date"""
    try:
        if isinstance(str_date, str):
            _day = datetime.strptime(str_date, '%Y-%m-%d').date()
            return _day
        elif isinstance(str_date, date):
            return str_date
    except:
        print('Error date')


# def OLD_prepare_workday(_date):     # TODO: moved to FUNC
#     if WorkDaySheet.objects.filter(date__gte=_date).count() < 14:
#         for n in range(14):
#             _day = TODAY + timedelta(days=n)
#             if _day.weekday() in (5, 6):
#                 status = False
#             else:
#                 status = True
#             WorkDaySheet.objects.update_or_create(date=_day, defaults={'status': status})
#
#         return WorkDaySheet.objects.get(date=_date)
#     else:
#         return False


def get_create_workday(_date):
    if WorkDaySheet.objects.filter(date=_date).exists():
        return WorkDaySheet.objects.get(date=_date)
    else:
        weekday = datetime.strptime(_date, '%Y-%m-%d').weekday()
        if weekday in (5, 6):
            _status = False
        else:
            _status = True
        return WorkDaySheet.objects.create(date=_date, status=_status)


def get_weekday(_date) -> str | None:
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


def prepare_driver_sheet(workday: WorkDaySheet):
    driver_list = User.objects.filter(isArchive=False, post=ASSETS.DRIVER)
    count_driver = len(driver_list)

    driver_sheet_list = DriverSheet.objects.filter(isArchive=False, date=workday)
    count_driver_sheet = len(driver_sheet_list)

    last_workday = WorkDaySheet.objects.filter(date__lt=workday.date, status=True).first()
    last_driver_sheet = DriverSheet.objects.filter(isArchive=False, date=last_workday)
    if count_driver > count_driver_sheet:

        if last_driver_sheet.exists():
            for driver in last_driver_sheet:
                DriverSheet.objects.get_or_create(date=workday,
                                                  driver=driver.driver,
                                                  status=driver.status)
        else:
            for driver in driver_list:
                DriverSheet.objects.get_or_create(date=workday, driver=driver)
        print('+')
    elif count_driver < count_driver_sheet:
        print('-')
    else:
        print('=')


def prepare_technic_sheet(workday: WorkDaySheet):
    technic_list = Technic.objects.filter(isArchive=False)
    count_technic = len(technic_list)

    technic_sheet_list = TechnicSheet.objects.filter(isArchive=False, date=workday)
    count_technic_sheet = len(technic_sheet_list)

    last_workday = WorkDaySheet.objects.filter(date__lt=workday.date, status=True).first()
    last_technic_sheet = TechnicSheet.objects.filter(isArchive=False, date=last_workday)
    driver_sheet_list = DriverSheet.objects.filter(isArchive=False, date=workday, status=True)

    autocomplete_technic_sheet(technic_sheet_list)

    if count_technic > count_technic_sheet:
        print('+')
        if last_technic_sheet.exists():
            for technic in last_technic_sheet:
                if technic.driver_sheet is None:
                    driver_sheet = None
                else:
                    driver_sheet = driver_sheet_list.filter(driver=technic.driver_sheet.driver).first()
                TechnicSheet.objects.get_or_create(date=workday,
                                                   technic=technic.technic,
                                                   status=technic.status,
                                                   driver_sheet=driver_sheet
                                                   )
        else:
            print('create')
            for technic in technic_list:
                driver_sheet = driver_sheet_list.filter(driver=technic.attached_driver).first()
                TechnicSheet.objects.get_or_create(date=workday,
                                                   technic=technic,
                                                   driver_sheet=driver_sheet
                                                   )
    elif count_technic < count_technic_sheet:
        print('-')
    else:
        print('=')


def autocomplete_technic_sheet(technic_sheet: TechnicSheet.objects):
    empty_technic_sheet = technic_sheet.filter(driver_sheet__isnull=True,
                                               technic__attached_driver__isnull=False
                                               )
    if empty_technic_sheet.exists():
        driver_sheet_list = DriverSheet.objects.filter(isArchive=False, status=True)
        for technic_sheet in empty_technic_sheet:
            driver_sheet = driver_sheet_list.filter(date=technic_sheet.date,
                                                    driver=technic_sheet.technic.attached_driver
                                                    ).first()
            technic_sheet.driver_sheet = driver_sheet
            technic_sheet.save()


def get_workload_dict(current_date=TODAY):
    _work_day = WorkDaySheet.objects.get(date=current_date)
    if _work_day.status:
        _technic_sheet_list = TechnicSheet.objects.filter(isArchive=False, status=True, date=_work_day,
                                                          driver_sheet__isnull=False, driver_sheet__status=True)
        workload_dict = _technic_sheet_list.values(
            'id', 'technic__title', 'driver_sheet_id', 'count_application'
        )
        return workload_dict
    else:
        return None


def get_free_technic_sheet_list(technic_title, current_date=TODAY, f_free=True):
    _work_day = WorkDaySheet.objects.get(date=current_date)
    if _work_day.status:
        free_technic_sheet_list = []
        workload_dict = get_workload_dict(current_date)
        for workload_item in workload_dict:
            if workload_item['technic__title'] == technic_title and f_free and workload_item['count_application'] == 0:
                free_technic_sheet_list.append(workload_item)
            elif workload_item['technic__title'] == technic_title and not f_free:
                free_technic_sheet_list.append(workload_item)
        return free_technic_sheet_list
    else:
        return None


def get_random_technic_sheet(free_tech_sheet_list: list):
    if free_tech_sheet_list:
        free_tech_sheet_list.sort(key=lambda item: item['count_application'])
        return free_tech_sheet_list[0]  # TODO: random choice
    else:
        return None


def get_random_free_technic_sheet(free_tech_sheet_list: list):
    if free_tech_sheet_list:
        return random.choice(free_tech_sheet_list)
    else:
        return None


def get_some_technic_sheet(technic_title, current_date: WorkDaySheet) -> TechnicSheet:
    free_technic_sheet_list = get_free_technic_sheet_list(technic_title, current_date.date)
    free_technic_sheet = get_random_free_technic_sheet(free_technic_sheet_list)
    if not free_technic_sheet:
        any_technic_sheet_list = get_free_technic_sheet_list(technic_title, current_date.date,
                                                             f_free=False)
        any_technic_sheet = get_random_technic_sheet(any_technic_sheet_list)
        return TechnicSheet.objects.get(id=any_technic_sheet.get('id'))
    else:
        return TechnicSheet.objects.get(id=free_technic_sheet.get('id'))


def get_short_technic_name_dict(current_date: WorkDaySheet) -> dict | None:
    if current_date.status:
        _technic_sheet = TechnicSheet.objects.filter(isArchive=False, status=True, driver_sheet__isnull=False,
                                                     driver_sheet__status=True, date=current_date)
        technic_titles_list = _technic_sheet.values_list('technic__title', flat=True).distinct()
        technic_titles_dict = {}
        for title in technic_titles_list:
            _title = str(title).replace(' ', '').replace('.', '')
            technic_titles_dict[_title] = title
        return technic_titles_dict
    else:
        return None


def get_short_technic_name(short_technic_name: str, current_date: WorkDaySheet) -> str | None:
    short_technic_name_dict = get_short_technic_name_dict(current_date)
    if short_technic_name_dict:
        return short_technic_name_dict[short_technic_name]
    else:
        return None


def calculate_technic_sheet_count_application(technic_sheet_list: QuerySet):
    if isinstance(technic_sheet_list, QuerySet):
        for technic_sheet_id in technic_sheet_list:
            _t_sh = TechnicSheet.objects.get(id=technic_sheet_id)
            _at_count = ApplicationTechnic.objects.filter(
                technic_sheet_id=technic_sheet_id,
                isChecked=False, is_cancelled=False).count()
            if _at_count > 0:
                _t_sh.count_application = _at_count - 1
                _t_sh.save()


def decrement_all_technic_sheet(current_date: WorkDaySheet):
    technic_sheet_list = TechnicSheet.objects.filter(isArchive=False, date=current_date)
    for technic_sheet in technic_sheet_list:
        technic_sheet.count_application = 0
        technic_sheet.save(update_fields=['count_application'])


def change_status_application(application_today_id: int):
    try:
        current_application_today = ApplicationToday.objects.get(id=application_today_id)
        _status = get_nxt_status(current_application_today.status)
        current_application_today.status = _status
        current_application_today.save(update_fields=['status'])
    except ApplicationToday.DoesNotExist as e:
        print(f'{e}')


def get_nxt_status(status: str):
    if status == ASSETS.ABSENT:
        return ASSETS.SAVED
    elif status == ASSETS.SAVED:
        return ASSETS.SUBMITTED
    elif status == ASSETS.SUBMITTED:
        return ASSETS.APPROVED
    elif status == ASSETS.APPROVED:
        return ASSETS.SEND
    elif status == ASSETS.SEND:
        return ASSETS.SEND
    # else:
    #     return ASSETS.ABSENT


def change_to_up_status(application_today_list, status: str):
    for application_today in application_today_list:
        if application_today.status == status:
            application_today.status = get_nxt_status(status)
            application_today.save(update_fields=['status'])


# def change_status_to_approved(application_today_list):
#     for application_today in application_today_list:
#         if application_today.status == ASSETS.SUBMITTED:
#             application_today.status = ASSETS.APPROVED
#             application_today.save(update_fields=['status'])
#
#
# def change_status_to_send(application_today_list):
#     for application_today in application_today_list:
#         if application_today.status == ASSETS.APPROVED:
#             application_today.status = ASSETS.SEND
#             application_today.save(update_fields=['status'])


def get_work_days():
    work_days = WorkDaySheet.objects.filter(
        Q(date__gt=TODAY - timedelta(days=2)) &
        Q(date__lt=TODAY + timedelta(days=4))
    ).reverse()
    return work_days


def get_prev_work_day(current_work_day) -> WorkDaySheet:
    prev_work_day = WorkDaySheet.objects.filter(date__lt=current_work_day,
                                                status=True).first()
    return prev_work_day


def get_next_work_day(current_work_day) -> WorkDaySheet:
    next_work_day = WorkDaySheet.objects.filter(date__gt=current_work_day,
                                                status=True).last()
    return next_work_day


def get_prepared_data(context: dict, current_day: date = TODAY) -> dict:
    _work_days = get_work_days().values()
    for work_day in _work_days:
        work_day['weekday'] = ASSETS.WEEKDAY[work_day['date'].weekday()][:3]

    context['work_days'] = _work_days
    context['today'] = TODAY
    context['prev_work_day'] = get_prev_work_day(current_day)
    context['next_work_day'] = get_next_work_day(current_day)
    context['weekday'] = get_weekday(current_day)
    context['edit_mode'] = get_edit_mode(current_day)
    # context['weekday'] = ASSETS.WEEKDAY[current_day.weekday()]
    return context


def prepare_sheets(work_day: WorkDaySheet):
    prepare_driver_sheet(work_day)
    prepare_technic_sheet(work_day)
    print('prepare_sheets OK')


def get_busiest_technic_sheet(work_day: WorkDaySheet):
    technic_sheet = TechnicSheet.objects.filter(date=work_day,
                                                driver_sheet__isnull=False,
                                                status=True,
                                                isArchive=False,
                                                count_application__gt=1)
    # print(f'{technic_sheet.values()}')

    return technic_sheet


def get_busiest_technic_title(work_day: WorkDaySheet) -> list:
    #   получения списка занятости technic sheet
    _out = []
    technic_sheet = TechnicSheet.objects.filter(date=work_day,
                                                driver_sheet__isnull=False,
                                                status=True,
                                                isArchive=False)
    technic_title_list = technic_sheet.values_list('technic__title', flat=True).distinct()
    for technic_title in technic_title_list:
        _out.append({
            'technic_title': technic_title,
            'free_technic_sheet_count': technic_sheet.filter(technic__title=technic_title,
                                                             count_application=0).count(),
            'total_technic_sheet_count': technic_sheet.filter(technic__title=technic_title).count(),
            'id_list': list(technic_sheet.filter(technic__title=technic_title).values_list('id', flat=True))
        })
    return _out


def get_conflict_technic_sheet(busiest_technic_title: list, priority_id_list: list, get_id_list=False) -> list:
    _out = []
    for _technic_sheet in busiest_technic_title:
        if _technic_sheet['free_technic_sheet_count'] == 0 and set(_technic_sheet['id_list']).intersection(
                priority_id_list):
            if get_id_list:
                _out.extend(_technic_sheet['id_list'])
            else:
                _out.append(_technic_sheet)
    return _out


def get_priority_id_list(work_day: WorkDaySheet) -> list:
    #   получения списка technic sheet id с нераспределенным приоритетом
    _out = []
    technic_sheet_list = TechnicSheet.objects.filter(date=work_day,
                                                     driver_sheet__isnull=False,
                                                     status=True,
                                                     isArchive=False)
    application_technic_list = ApplicationTechnic.objects.filter(application_today__date=work_day,
                                                                 technic_sheet__in=technic_sheet_list,
                                                                 isArchive=False,
                                                                 is_cancelled=False,
                                                                 isChecked=False)
    for technic_sheet in technic_sheet_list:
        _id = technic_sheet.id
        _count_application = application_technic_list.filter(technic_sheet=technic_sheet).count()
        _count_set_priority_list = application_technic_list.filter(
            technic_sheet=technic_sheet).values_list('priority', flat=True).distinct().count()
        if _count_application != _count_set_priority_list:
            _out.append(_id)
    return _out


def get_status_list_application_today(work_day: WorkDaySheet) -> dict:
    _out = {ASSETS.ABSENT: [],
            ASSETS.SAVED: [],
            ASSETS.SUBMITTED: [],
            ASSETS.APPROVED: [],
            ASSETS.SEND: []}
    application_today_list = ApplicationToday.objects.filter(date=work_day, isArchive=False)
    for application in application_today_list:
        if application.status == ASSETS.ABSENT:
            _out[ASSETS.ABSENT].append(application.id)
        elif application.status == ASSETS.SAVED:
            _out[ASSETS.SAVED].append(application.id)
        elif application.status == ASSETS.SUBMITTED:
            _out[ASSETS.SUBMITTED].append(application.id)
        elif application.status == ASSETS.APPROVED:
            _out[ASSETS.APPROVED].append(application.id)
        elif application.status == ASSETS.SEND:
            _out[ASSETS.SEND].append(application.id)
    return _out


def set_color_for_list(l: list) -> dict:
    random.shuffle(ASSETS.COLORS)
    _colors = ASSETS.COLORS
    _out = {}
    for _id, color in zip(l, _colors):
        _out[int(_id)] = color
    return _out


def sorting_application_status(item1, item2):
    if item1 == item2 and item1 in ASSETS.APPLICATION_STATUS_set:
        return 0
    if item1 in (None, ASSETS.ABSENT, ASSETS.SAVED, ASSETS.SUBMITTED, ASSETS.APPROVED) and item2 in (ASSETS.SEND,):
        return -1
    if item1 in (None, ASSETS.ABSENT, ASSETS.SAVED, ASSETS.SUBMITTED) and item2 in (ASSETS.SEND, ASSETS.APPROVED):
        return -1
    if item1 in (None, ASSETS.ABSENT, ASSETS.SAVED) and item2 in (ASSETS.SEND, ASSETS.SUBMITTED, ASSETS.APPROVED):
        return -1
    if item1 in (None, ASSETS.ABSENT,) and item2 in (ASSETS.SEND, ASSETS.SAVED, ASSETS.SUBMITTED, ASSETS.APPROVED):
        return -1
    if item1 in (None,) and item2 in (ASSETS.SEND, ASSETS.SAVED, ASSETS.SUBMITTED, ASSETS.APPROVED, ASSETS.ABSENT):
        return -1


def change_is_cancelled(app_tech_id):
    if app_tech_id:
        try:
            _app_tech = ApplicationTechnic.objects.get(id=app_tech_id)
        except ApplicationTechnic.DoesNotExist:
            return -1
        if _app_tech.is_cancelled:
            _app_tech.isChecked = False
            _app_tech.is_cancelled = False
            _app_tech.description = _app_tech.description.replace(ASSETS.MESSAGES['reject'], "")
            _app_tech.technic_sheet.increment_count_application()
            # _app_tech.technic_sheet.save()
            _app_tech.save()
        else:
            _app_tech.isChecked = False
            _app_tech.is_cancelled = True
            _app_tech.description = ASSETS.MESSAGES['reject'] + _app_tech.description
            _app_tech.technic_sheet.decrement_count_application()
            # _app_tech.technic_sheet.save()
            _app_tech.save()
        return 0


def change_is_checked(app_tech_id, application_today_id):
    if app_tech_id and application_today_id:
        try:
            _app_tech = ApplicationTechnic.objects.get(id=app_tech_id)
            _app_today = ApplicationToday.objects.get(id=application_today_id)
        except:
            return -1

        if _app_tech.is_cancelled:
            _app_tech.is_cancelled = False
            _app_tech.description = _app_tech.description.replace(ASSETS.MESSAGES['reject'], "")
            _app_tech.technic_sheet.increment_count_application()
            _app_tech.technic_sheet.save()
            _app_tech.save()

        str_constr_site = f"{_app_tech.application_today.construction_site.address} ({_app_tech.application_today.construction_site.foreman.last_name}):\n"
        str_desc = str_constr_site + _app_tech.description + '\n'

        if not _app_tech.isChecked:
            _new_app_tech, created = ApplicationTechnic.objects.get_or_create(technic_sheet=_app_tech.technic_sheet,
                                                                              application_today=_app_today,
                                                                              id_orig_app=_app_tech.id)
            # _new_app_tech.id_orig_app = _app_tech.id
            _new_app_tech.description = _new_app_tech.description + str_desc if _new_app_tech.description else str_desc
            _new_app_tech.save()

            _app_tech.isChecked = True
            _app_tech.save()
        elif _app_tech.isChecked:
            _app_tech.isChecked = False
            _app_tech.save()
            _old_at = ApplicationTechnic.objects.get(application_today=_app_today,
                                                     isArchive=False,
                                                     technic_sheet=_app_tech.technic_sheet,
                                                     id_orig_app=_app_tech.id)
            _old_at.description = _old_at.description.replace(str_desc, '')
            _old_at.save()
            if not _old_at.description:
                _old_at.delete()
        return 0


def get_supply_technic_list() -> Technic:
    _out = Technic.objects.filter(isArchive=False, supervisor_technic=ASSETS.SUPPLY)
    return _out


def get_table_working_technic_sheet(current_day: WorkDaySheet):
    _out = []
    _technic_sheet = TechnicSheet.objects.filter(isArchive=False, date=current_day)
    # _out = _technic_sheet.order_by('driver_sheet__driver__last_name')
    _out = _technic_sheet.order_by('technic__title')
    return _out


def set_prepare_filter(request):
    if request.POST.get('operation') == 'hide':
        _hide_panel = 'change'
    else:
        _hide_panel = None

    is_show_saved_app = request.POST.get('is_show_saved_app')
    is_show_saved_app = is_show_saved_app.capitalize() if is_show_saved_app else None

    is_show_absent_app = request.POST.get('is_show_absent_app')
    is_show_absent_app = is_show_absent_app.capitalize() if is_show_absent_app else None

    is_show_technic_app = request.POST.get('is_show_technic_app')
    is_show_technic_app = is_show_technic_app.capitalize() if is_show_technic_app else None

    is_show_material_app = request.POST.get('is_show_material_app')
    is_show_material_app = is_show_material_app.capitalize() if is_show_material_app else None

    filter_construction_site = request.POST.get('filter_construction_site')
    filter_construction_site = filter_construction_site if filter_construction_site is not None else 0

    filter_foreman = request.POST.get('filter_foreman')
    filter_foreman = filter_foreman if filter_foreman is not None else 0

    filter_technic = request.POST.get('filter_technic')
    filter_technic = filter_technic if filter_technic != '' else None

    sort_by = request.POST.get('sort_by')
    sort_by = sort_by if sort_by != '' else None

    try:
        _user = User.objects.get(id=request.user.id)
        if is_show_saved_app:
            _user.is_show_saved_app = is_show_saved_app
        if is_show_absent_app:
            _user.is_show_absent_app = is_show_absent_app
        if is_show_technic_app:
            _user.is_show_technic_app = is_show_technic_app
        if is_show_material_app:
            _user.is_show_material_app = is_show_material_app
        if filter_construction_site:
            _user.filter_construction_site = filter_construction_site
        if filter_foreman:
            _user.filter_foreman = filter_foreman
        if _hide_panel:
            _user.is_show_panel = False if _user.is_show_panel else True
        _user.filter_technic = filter_technic
        _user.sort_by = sort_by

        _user.save()
    except User.DoesNotExist:
        return -1


def get_prepare_filter(context):
    foreman_list = User.objects.filter(isArchive=False, post=ASSETS.FOREMAN)
    construction_site_list = ConstructionSite.objects.filter(isArchive=False, status=True)
    technic_list = Technic.objects.filter(isArchive=False).values_list('title', flat=True).distinct()
    sort_by_list = ASSETS.SORT_BY
    context['filter_foreman_list'] = foreman_list
    context['filter_construction_site_list'] = construction_site_list
    context['filter_technic_list'] = technic_list
    context['sort_by_list'] = sort_by_list

    change_reception_apps_mode_auto()

    return context


def send_messages(chat_id, messages):
    T.BOT.send_message(chat_id=chat_id,
                       text=messages,
                       parse_mode='html')


def get_user_key(user_id) -> str | None:
    try:
        _user = User.objects.get(pk=user_id)
        _key = random.randint(100, 999)
        return f'{_key}{_user.id}'
    except User.DoesNotExist:
        return None


def send_application_for_driver(current_day: WorkDaySheet, messages=None, application_today_id=None):
    _out = []
    send_flag, created = Parameter.objects.get_or_create(
        name=VAR.VAR_APPLICATION_SEND['name'],
        title=VAR.VAR_APPLICATION_SEND['title'],
        date=current_day.date)
    driver_list = TechnicSheet.objects.filter(date=current_day, status=True, driver_sheet__status=True, isArchive=False)

    m_day = f'{ASSETS.WEEKDAY[current_day.date.weekday()]}, {current_day.date.day} {ASSETS.MONTHS[current_day.date.month - 1]}'
    # print(m_day)
    if application_today_id is None:
        application_today = ApplicationToday.objects.filter(isArchive=False, date=current_day, status=ASSETS.SEND)
    else:
        application_today = ApplicationToday.objects.filter(id=application_today_id, date=current_day)

    application_technic_list = ApplicationTechnic.objects.filter(application_today__in=application_today,
                                                                 isArchive=False, is_cancelled=False, isChecked=False)

    driver_list = driver_list.filter(id__in=application_technic_list.values_list('technic_sheet_id', flat=True))

    for driver in driver_list:
        _out.append((
            driver,
            application_technic_list.filter(technic_sheet=driver).order_by('priority')
        ))

    for drv, apps in _out:
        if send_flag.flag:
            mess = f'{drv.driver_sheet.driver.last_name} {drv.driver_sheet.driver.first_name}\nОбновленная заявка на:\n{m_day}\n\n'
        else:
            mess = f'{drv.driver_sheet.driver.last_name} {drv.driver_sheet.driver.first_name}\nЗаявка на:\n{m_day}\n\n'
        for app in apps:
            if app.application_today.construction_site.foreman:
                mess += f'\t{app.priority}) {app.application_today.construction_site.address} ({app.application_today.construction_site.foreman.last_name})\n'
            else:
                mess += f'\t{app.priority}) {app.application_today.construction_site.address}\n'
            mess += f'{app.description}\n\n'
        if messages:
            mess = messages
        if drv.driver_sheet.driver.telegram_id_chat:
            send_messages(drv.driver_sheet.driver.telegram_id_chat, mess)


def send_application_for_foreman(current_day: WorkDaySheet, messages=None, application_today_id=None):
    _out = []
    send_flag, created = Parameter.objects.get_or_create(
        name=VAR.VAR_APPLICATION_SEND['name'],
        title=VAR.VAR_APPLICATION_SEND['title'],
        date=current_day.date)

    m_day = f'{ASSETS.WEEKDAY[current_day.date.weekday()]}, {current_day.date.day} {ASSETS.MONTHS[current_day.date.month - 1]}'
    # print(m_day)
    if application_today_id is None:
        application_today = ApplicationToday.objects.filter(isArchive=False, date=current_day, status=ASSETS.SEND)
    else:
        application_today = ApplicationToday.objects.filter(id=application_today_id, date=current_day)

    foreman_list = User.objects.filter(isArchive=False, post__in=(ASSETS.FOREMAN, ASSETS.MASTER, ASSETS.SUPPLY))
    # application_technic_list = ApplicationTechnic.objects.filter(application_today__in=application_today,
    #                                                              isArchive=False, is_cancelled=False, isChecked=False)

    # print(foreman_list)

    for foreman in foreman_list:
        if foreman.post == ASSETS.FOREMAN:
            _out.append((foreman, application_today.filter(construction_site__foreman=foreman)))
        elif foreman.post == ASSETS.MASTER:
            foreman = User.objects.get(pk=foreman.supervisor_user_id)
            _out.append((foreman, application_today.filter(construction_site__foreman=foreman)))
    # print(_out)

    for foreman, apps in _out:
        if send_flag.flag:
            mess = f"Повторное уведомление:\n{m_day}\n"
        else:
            mess = f"{m_day}\n"
        for app in apps:
            mess += f"Заявка на {app.construction_site.address} одобрена\n"

        if messages:
            mess = messages
        # print(mess)
        # send_messages('385035447', mess)
        if foreman.telegram_id_chat:
            send_messages(foreman.telegram_id_chat, mess)


def send_application_for_admin(current_day: WorkDaySheet, messages=None, application_today_id=None):
    _out = []
    send_flag, created = Parameter.objects.get_or_create(
        name=VAR.VAR_APPLICATION_SEND['name'],
        title=VAR.VAR_APPLICATION_SEND['title'],
        date=current_day.date)

    m_day = f'{ASSETS.WEEKDAY[current_day.date.weekday()]}, {current_day.date.day} {ASSETS.MONTHS[current_day.date.month - 1]}'
    # print(m_day)
    admin_list = User.objects.filter(isArchive=False, post=ASSETS.ADMINISTRATOR)

    if application_today_id is None:
        if send_flag.flag:
            mess = f"Заявки на:\n{m_day} отправлены повторно"
        else:
            mess = f"Заявки на:\n{m_day} отправлены"
        if messages:
            mess = messages
        for admin in admin_list:
            if admin.telegram_id_chat:
                send_messages(admin.telegram_id_chat, mess)
    else:
        application_today = ApplicationToday.objects.filter(id=application_today_id, date=current_day)

        for app in application_today:
            if app.construction_site.foreman:
                cs = f'{app.construction_site.address} ({app.construction_site.foreman})'
            else:
                cs = f'{app.construction_site.address}'

            if send_flag.flag:
                mess = f"Заявка на:\n{m_day}\nобъект: {cs} отправлена повторно"
            else:
                mess = f"Заявка на:\n{m_day}\nобъект: {cs} отправлена"

            if messages:
                mess = messages
            for admin in admin_list:
                if admin.telegram_id_chat:
                    send_messages(admin.telegram_id_chat, mess)


def send_application_for_all(current_day: WorkDaySheet, messages=None, application_today_id=None):
    send_application_for_driver(current_day, messages, application_today_id)
    send_application_for_foreman(current_day, messages, application_today_id)
    send_application_for_admin(current_day, messages, application_today_id)


def copy_application(id_application_today, _target_day, default_status=ASSETS.SAVED):
    try:
        target_day = WorkDaySheet.objects.get(date=_target_day)
        current_application = ApplicationToday.objects.get(id=id_application_today)

        new_application, _ = ApplicationToday.objects.get_or_create(
            date=target_day, status=default_status, description=current_application.description,
            construction_site=current_application.construction_site)

        current_application_material = ApplicationMaterial.objects.filter(application_today=current_application)
        if current_application_material.exists():
            new_application_material, _ = ApplicationMaterial.objects.get_or_create(application_today=new_application)
            new_application_material.description = current_application_material.first().description
            new_application_material.save()

        current_application_technic = ApplicationTechnic.objects.filter(application_today=current_application)

        for tech_app in current_application_technic:
            if tech_app.technic_sheet:
                target_tech_sheet = TechnicSheet.objects.filter(date=target_day,
                                                                status=True,
                                                                isArchive=False,
                                                                technic=tech_app.technic_sheet.technic)
                if target_tech_sheet.exists():
                    new_app_tech, _ = ApplicationTechnic.objects.get_or_create(
                        application_today=new_application,
                        technic_sheet=target_tech_sheet.first())
                    new_app_tech.description = tech_app.description
                    new_app_tech.save()
                    target_tech_sheet.first().increment_count_application()

    except (WorkDaySheet.DoesNotExist, ApplicationToday.DoesNotExist):
        print('COPY ERROR')


def set_spec_task(technic_sheet_id):
    construction_site, _ = ConstructionSite.objects.get_or_create(address=ASSETS.CS_SPEC_TITLE)
    try:
        technic_sheet = TechnicSheet.objects.get(id=technic_sheet_id)
        current_day = technic_sheet.date
        application_today, _ = ApplicationToday.objects.get_or_create(construction_site=construction_site,
                                                                      date=current_day,
                                                                      status=ASSETS.SUBMITTED)

        application_technic, at_created = ApplicationTechnic.objects.get_or_create(application_today=application_today,
                                                                                   technic_sheet=technic_sheet)
        if at_created:
            technic_sheet.increment_count_application()
        application_technic.description = ASSETS.CS_SPEC_DEFAULT_DESC
        application_technic.save()

    except TechnicSheet.DoesNotExist:
        print('SET_SPEC_TASK ERROR')


def get_edit_mode(_date: date):
    if _date == TODAY:
        return ASSETS.EDIT_MODE_CURRENT
    elif _date < TODAY:
        return ASSETS.EDIT_MODE_ARCHIVE
    elif _date > TODAY:
        return ASSETS.EDIT_MODE_FUTURE
    else:
        return None


def check_application_today(app_today: ApplicationToday, default_status=None):
    """ if empty - delete or save """
    _at_desc = app_today.description is not None and app_today.description != ''
    _at_at = ApplicationTechnic.objects.filter(application_today=app_today).exists()
    _at_am = ApplicationMaterial.objects.filter(application_today=app_today).exists()
    if any((_at_desc, _at_at, _at_am)):
        if default_status:
            app_today.status = default_status
        app_today.save()
    else:
        app_today.delete()


def prepare_variables():
    """ Подготовка переменных"""
    variables_list = VAR.VARIABLES_LIST
    error = 0
    for variable in variables_list:
        try:
            Parameter.objects.get_or_create(
                title=variable.get('title'),
                name=variable.get('name'),
                value=variable.get('value'),
                flag=variable.get('flag', False),
                description=variable.get('description'),
                time=variable.get('time'),
                date=variable.get('date'),
                permissions=variable.get('permissions')
            )
        except ValueError:
            error += 1
    return error


def change_reception_apps_mode_auto():
    """ Автоматическое переключение режима приема заявок"""
    try:
        work_day = WorkDaySheet.objects.get(date=TODAY)
    except WorkDaySheet.DoesNotExist:
        return -1
    try:
        var_time_recept_apps = Parameter.objects.get(name=VAR.VAR_TIME_RECEPTION_OF_APPS['name'])
    except Parameter.DoesNotExist:
        return -1

    if var_time_recept_apps.date != work_day.date or var_time_recept_apps.flag:
        var_time_recept_apps.date = work_day.date
        var_time_recept_apps.flag = True
        var_time_recept_apps.save()
        if var_time_recept_apps.time < datetime.now().time():
            work_day.is_only_read = True
            work_day.save()
        else:
            work_day.is_only_read = False
            work_day.save()


def change_reception_apps_mode_manual(workday: WorkDaySheet, is_recept_apps):
    """ Ручное переключение режима приема заявок"""
    if is_recept_apps:
        workday.is_only_read = True
        workday.save(update_fields=['is_only_read'])
    else:
        workday.is_only_read = False
        workday.save(update_fields=['is_only_read'])

    try:
        _var_recept_apps = Parameter.objects.get(name=VAR.VAR_TIME_RECEPTION_OF_APPS['name'])
        _var_recept_apps.flag = False
        _var_recept_apps.save(update_fields=['flag'])
    except Parameter.DoesNotExist:
        pass
