from django.http import HttpResponseRedirect

from dashboard.models import WorkDaySheet, DriverSheet, TechnicSheet, ConstructionSite, ApplicationMaterial
from django.db.models.query import QuerySet
from django.db.models import Q
from dashboard.models import ApplicationToday, ApplicationTechnic
from dashboard.models import Technic
# from dashboard.models import Administrator, Foreman, Master, Mechanic, Driver, Supply, Employee
from dashboard.models import User
from dashboard.models import Parameter
from logger import getLogger

#   ------------------------------------------------------------------------------------------------------------------


from datetime import date, timedelta, datetime
import random
import config.endpoints as ENDPOINTS
import dashboard.assets as ASSETS
import dashboard.telegram_bot as T
import dashboard.variables as VAR
import dashboard.services.user as USERS_SERVICE
import dashboard.services.technic as TECHNIC_SERVICE
import dashboard.services.construction_site as CONSTR_SITE_SERVICE
import dashboard.services.work_day_sheet as WORK_DAY_SERVICE
import dashboard.services.driver_sheet as DRIVER_SHEET_SERVICE
import dashboard.services.technic_sheet as TECHNIC_SHEET_SERVICE
import dashboard.services.dashboard as DASHBOARD_SERVICE
import dashboard.services.application_today as APP_TODAY_SERVICE
import dashboard.services.application_technic as APP_TECHNIC_SERVICE
import dashboard.services.application_material as APP_MATERIAL_SERVICE

#   ------------------------------------------------------------------------------------------------------------------
log = getLogger(__name__)

TODAY = date.today()
NOW = datetime.now().time()
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


def get_weekday(_date: date) -> str | None:
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


def decrement_all_technic_sheet(current_date: WorkDaySheet):
    technic_sheet_list = TechnicSheet.objects.filter(isArchive=False, date=current_date)
    for technic_sheet in technic_sheet_list:
        technic_sheet.count_application = 0
        technic_sheet.save(update_fields=['count_application'])


def get_prepared_data(context: dict, current_day: date = TODAY) -> dict:
    """
    Подготовка и получения глобальных данных
    :param context:
    :param current_day:
    :return:
    """
    workdays = WORK_DAY_SERVICE.get_range_workdays(start_date=TODAY, before_days=1, after_days=3).reverse().values()
    for workday in workdays:
        workday['weekday'] = ASSETS.WEEKDAY[workday['date'].weekday()][:3]
    context['work_days'] = workdays

    context['today'] = TODAY
    context['prev_work_day'] = WORK_DAY_SERVICE.get_prev_workday(current_day)
    context['next_work_day'] = WORK_DAY_SERVICE.get_next_workday(current_day)
    context['weekday'] = get_weekday(current_day)
    context['edit_mode'] = get_edit_mode(current_day)
    change_reception_apps_mode_auto()
    return context


def prepare_sheets(work_day: WorkDaySheet):
    DRIVER_SHEET_SERVICE.prepare_driver_sheet(workday=work_day)
    TECHNIC_SHEET_SERVICE.prepare_technic_sheets(workday=work_day)
    log.info(f"Prepare sheets done")


def get_busiest_technic_title(technic_sheet: QuerySet[TechnicSheet]) -> list:
    """
    Получения списка с информацией о загруженности technic_title
    :param technic_sheet:
    :return: [{}, {}]
    """
    out = []
    technic_sheet = technic_sheet.exclude(applicationtechnic__application_today__status=ASSETS.SAVED)
    technic_title_list = technic_sheet.values_list('technic__title', flat=True).distinct()

    for technic_title in technic_title_list:
        technic__title_list = technic_sheet.filter(technic__title=technic_title).values('id', 'count_application')
        out.append({
            'technic_title': technic_title,
            'free_technic_sheet_count': technic__title_list.filter(count_application=0).count(),
            'total_technic_sheet_count': technic__title_list.count(),
            'id_list': list(technic__title_list.values_list('id', flat=True))
        })
    return out


def get_conflict_list_of_technic_sheet(busiest_technic_title: list, priority_id_list: set, get_only_id_list=False) -> list:
    """
    Получить список конфликтов technic_sheet
    :param busiest_technic_title: список с информацией о загруженности technic_title
    :param priority_id_list: сет technic_sheet_id с нераспределенным приоритетом
    :param get_only_id_list: True - получить только id; False - получить более подробную информацию
    :return: [{}, {}, ...]
    """
    out = []
    for _technic_sheet in busiest_technic_title:
        if _technic_sheet['free_technic_sheet_count'] == 0 and set(_technic_sheet['id_list']).intersection(
                priority_id_list):
            if get_only_id_list:
                out.extend(_technic_sheet['id_list'])
            else:
                out.append(_technic_sheet)
    return out


def get_priority_id_list(technic_sheet: QuerySet[TechnicSheet]) -> set:
    """
    Получения сета technic_sheet_id с нераспределенным приоритетом
    :param technic_sheet:
    :return: set(.., ...)
    """
    technic_sheet = technic_sheet.exclude(applicationtechnic__application_today__status=ASSETS.SAVED)
    technic_sheet_list_id_list = technic_sheet.filter(count_application__gt=0, driver_sheet__status=True).values('id')
    application_technic_list = tuple(APP_TECHNIC_SERVICE.get_apps_technic_queryset(
        technic_sheet__in=technic_sheet_list_id_list,
        isArchive=False,
        is_cancelled=False,
        isChecked=False
    ).values(
        'technic_sheet__id',
        'priority'
    ))
    out = {item['technic_sheet__id'] for item in application_technic_list if application_technic_list.count(item) > 1}
    return out


def set_color_for_list(some_list: list) -> dict:
    """
    Привязка цвета для каждого элемента из списка some_list
    :param some_list:
    :return:
    """
    colors = ASSETS.COLORS[:]
    random.shuffle(colors)
    out = {int(id_): color for id_, color in zip(some_list, colors)}
    return out


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


def accept_app_tech_to_supply(app_tech_id, application_today_id):
    """
    Принять заявку ApplicationTechnic(id=app_tech_id) для supply
    :param app_tech_id:
    :param application_today_id:
    :return:
    """
    application_technic = APP_TECHNIC_SERVICE.get_app_technic(pk=app_tech_id)
    application_today = APP_TODAY_SERVICE.get_apps_today(pk=application_today_id)
    if all((application_technic, application_today)):

        if application_technic.is_cancelled:
            application_technic.is_cancelled = False
            application_technic.description = application_technic.description.replace(ASSETS.MESSAGES['reject'], "")
            application_technic.technic_sheet.increment_count_application()
            application_technic.technic_sheet.save()
            application_technic.save()

        str_constr_site = f"{application_technic.application_today.construction_site.address} ({application_technic.application_today.construction_site.foreman.last_name}):\n"
        str_desc = str_constr_site + application_technic.description + '\n'

        if not application_technic.isChecked:
            _new_app_tech, created = ApplicationTechnic.objects.get_or_create(
                technic_sheet=application_technic.technic_sheet,
                application_today=application_today,
                id_orig_app=application_technic.id)
            _new_app_tech.description = _new_app_tech.description + str_desc if _new_app_tech.description else str_desc
            _new_app_tech.save()

            application_technic.isChecked = True
            application_technic.save()
        elif application_technic.isChecked:
            application_technic.isChecked = False
            application_technic.save()

            _old_at = APP_TECHNIC_SERVICE.get_app_technic(
                application_today=application_today,
                isArchive=False,
                technic_sheet=application_technic.technic_sheet,
                id_orig_app=application_technic.id
            )
            _old_at.description = _old_at.description.replace(str_desc, '')
            _old_at.save()
            if not _old_at.description:
                _old_at.delete()


def get_table_working_technic_sheet(current_day: WorkDaySheet):
    """
    Получить таблицу загруженность для dashboard
    :param current_day:
    :return:
    """
    _technic_sheet = TECHNIC_SHEET_SERVICE.get_technic_sheet_queryset(
        select_related=('driver_sheet__driver', 'technic__attached_driver'),
        isArchive=False,
        date=current_day
    )
    # _out = _technic_sheet.order_by('driver_sheet__driver__last_name')
    return _technic_sheet.order_by('technic__title')


def set_data_for_filter(request):
    """
    Установка параметров фильтрации
    :param request:
    :return:
    """
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

    _user = USERS_SERVICE.get_user(pk=request.user.id)
    if _user:
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


def prepare_data_for_filter(context: dict) -> dict:
    """
    Подготовка и получения данных для фильтра
    :param context:
    :return:
    """
    foreman_list = USERS_SERVICE.get_user_queryset(post=ASSETS.FOREMAN).values(
        'id',
        'last_name',
        'first_name'
    )
    construction_site_list = CONSTR_SITE_SERVICE.get_construction_site_queryset(
        status=True,
        select_related=('foreman',),
        order_by=('address',)
    )

    technic_list = TECHNIC_SERVICE.get_technics_queryset(
        isArchive=False
    ).values_list('title', flat=True).distinct()

    sort_by_list = ASSETS.SORT_BY

    context['filter_foreman_list'] = foreman_list
    context['filter_construction_site_list'] = construction_site_list
    context['filter_technic_list'] = technic_list
    context['sort_by_list'] = sort_by_list
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
def send_application_by_telegram_for_foreman(current_day: WorkDaySheet, messages=None, application_today_id=None):
    all_already_send = current_day.is_all_application_send
    template_date = f'{ASSETS.WEEKDAY[current_day.date.weekday()]}, {current_day.date.day} {ASSETS.MONTHS[current_day.date.month - 1]}'
    foreman_list = USERS_SERVICE.get_user_queryset(
        isArchive=False,
        post__in=(ASSETS.FOREMAN, ASSETS.MASTER, ASSETS.SUPPLY)
    ).values(
        'id',
        'last_name',
        'first_name',
        'post',
        'supervisor_user_id',
        'telegram_id_chat'
    )

    if application_today_id:
        application_today = APP_TODAY_SERVICE.get_apps_today_queryset(
            select_related=('construction_site__foreman',),
            pk=application_today_id)
    else:
        application_today = APP_TODAY_SERVICE.get_apps_today_queryset(
            select_related=('construction_site__foreman',),
            isArchive=False, date=current_day, status=ASSETS.SEND)

    for item in foreman_list:
        if item['post'] == ASSETS.FOREMAN:
            foreman_id = item['id']
        else:
            foreman_id = item['supervisor_user_id']
        if foreman_id:
            app_today = application_today.filter(construction_site__foreman_id=foreman_id)
        else:
            app_today = application_today.filter(construction_site__address=ASSETS.CS_SUPPLY_TITLE)
        item['applications'] = app_today.values(
            'construction_site__address',
            'is_application_send'
        )

    for item in foreman_list:
        if all_already_send:
            msg = f"Повторное уведомление:\n{template_date}\n"
        else:
            msg = f"{template_date}\n"
        if item['applications']:
            for app in item['applications']:
                if app['is_application_send']:
                    msg = f"Повторное уведомление:\n{template_date}\n"
                else:
                    msg = msg
                msg += f"Заявка на {app['construction_site__address']} одобрена\n"
            if item['telegram_id_chat']:
                send_messages_by_telegram(chat_id=item['telegram_id_chat'], messages=msg)


def send_application_by_telegram_for_admin(current_day: WorkDaySheet, messages=None, application_today_id=None):
    template_date = f'{ASSETS.WEEKDAY[current_day.date.weekday()]}, {current_day.date.day} {ASSETS.MONTHS[current_day.date.month - 1]}'
    administrators_list = USERS_SERVICE.get_user_queryset(isArchive=False, post=ASSETS.ADMINISTRATOR)

    if current_day.is_all_application_send:
        msg = f"Заявки на:\n{template_date} отправлены повторно"
    else:
        msg = f"Заявки на:\n{template_date} отправлены"

    if application_today_id:
        app_today = APP_TODAY_SERVICE.get_apps_today(pk=application_today_id)
        if app_today:
            if app_today.construction_site.foreman:
                msg_constr_site = f'{app_today.construction_site.address} ({app_today.construction_site.foreman})'
            else:
                msg_constr_site = f'{app_today.construction_site.address}'

            if app_today.is_application_send:
                msg = f"Заявка на:\n{template_date}\nобъект: {msg_constr_site} отправлена повторно"
            else:
                msg = f"Заявка на:\n{template_date}\nобъект: {msg_constr_site} отправлена"

    messages = messages if messages else msg

    [send_messages_by_telegram(admin.telegram_id_chat, messages)
     for admin in administrators_list if admin.telegram_id_chat]


def send_application_by_telegram_for_all(current_day: WorkDaySheet, messages=None, application_today_id=None):
    """
    Отправка заявок всем пользователям через Telegram
    :param current_day:
    :param messages:
    :param application_today_id:
    :return:
    """
    send_application_by_telegram_for_driver(current_day, messages, application_today_id)
    send_application_by_telegram_for_foreman(current_day, messages, application_today_id)
    send_application_by_telegram_for_admin(current_day, messages, application_today_id)
    if application_today_id:
        APP_TODAY_SERVICE.get_apps_today(pk=application_today_id).send_application()
    else:
        current_day.send_all_application()


def copy_application_to_target_day(id_application_today, _target_day, default_status=ASSETS.SAVED):
    """
    Копирование заявки ApplicationToday(id=id_application_today) на _target_day
    :param id_application_today:
    :param _target_day:
    :param default_status: saved | submitted
    :return:
    """
    target_day = WORK_DAY_SERVICE.get_workday(_target_day)
    current_application = APP_TODAY_SERVICE.get_apps_today(pk=id_application_today)

    new_application, _ = ApplicationToday.objects.get_or_create(
        date=target_day, status=default_status, description=current_application.description,
        construction_site=current_application.construction_site)

    current_application_material = APP_MATERIAL_SERVICE.get_apps_material_queryset(
        application_today=current_application)
    if current_application_material.exists():
        new_application_material, _ = ApplicationMaterial.objects.get_or_create(application_today=new_application)
        new_application_material.description = current_application_material.first().description
        new_application_material.save()

    current_application_technic = APP_TECHNIC_SERVICE.get_apps_technic_queryset(
        select_related=('technic_sheet__technic',),
        application_today=current_application)

    for tech_app in current_application_technic:
        if tech_app.technic_sheet:
            target_technic_sheet = TECHNIC_SHEET_SERVICE.get_technic_sheet(
                date=target_day,
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


def get_view_mode(_date: date) -> str:
    """
    Получить режим отображения
    :param _date:
    :return:
    """
    if _date == TODAY:
        return ASSETS.VIEW_MODE_CURRENT
    elif _date < TODAY:
        return ASSETS.VIEW_MODE_ARCHIVE
    elif _date > TODAY:
        return ASSETS.VIEW_MODE_FUTURE
    else:
        return 'None'


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


def change_reception_apps_mode_auto():  # TODO: move to service
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


def is_valid_get_request(value: str) -> bool:
    """
    Проверка : value is not None and value != ''
    :param value:
    :return:
    """
    if value is not None and value != '':
        return True
    else:
        return False
