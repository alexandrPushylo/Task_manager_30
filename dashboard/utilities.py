from django.http import HttpResponseRedirect
from config.creds import USE_TELEGRAM
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
import dashboard.services.parametr as PARAMETER_SERVICE

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


def get_prepared_data(context: dict, current_workday: WorkDaySheet) -> dict:
    """
    Подготовка и получения глобальных данных
    :param context:
    :param current_workday:
    :return:
    """
    workdays = WORK_DAY_SERVICE.get_range_workdays(start_date=TODAY, before_days=1, after_days=3).reverse().values()
    for workday in workdays:
        workday['weekday'] = ASSETS.WEEKDAY[workday['date'].weekday()][:3]
    context['work_days'] = workdays

    context['today'] = TODAY
    context['prev_work_day'] = WORK_DAY_SERVICE.get_prev_workday(current_workday.date)
    context['next_work_day'] = WORK_DAY_SERVICE.get_next_workday(current_workday.date)
    context['weekday'] = get_weekday(current_workday.date)
    context['VIEW_MODE'] = get_view_mode(current_workday.date)
    context['ACCEPT_MODE'] = get_accept_mode(workday=current_workday)
    return context


def prepare_sheets(work_day: WorkDaySheet):
    DRIVER_SHEET_SERVICE.prepare_driver_sheet(workday=work_day)
    TECHNIC_SHEET_SERVICE.prepare_technic_sheets(workday=work_day)
    log.info("Prepare sheets done")


def get_busiest_technic_title(technic_sheet: QuerySet[TechnicSheet]) -> list:
    """
    Получения списка с информацией о загруженности technic_title
    :param technic_sheet:
    :return: [{}, {}]
    """
    out = []
    technic_sheet = technic_sheet.exclude(
        applicationtechnic__application_today__status=ASSETS.ApplicationTodayStatus.SAVED.title
    )
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


def get_conflict_list_of_technic_sheet(busiest_technic_title: list, priority_id_list: set,
                                       get_only_id_list=False) -> list:
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
    technic_sheet = technic_sheet.exclude(
        applicationtechnic__application_today__status=ASSETS.ApplicationTodayStatus.SAVED.title
    )
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


def sorting_application_status(item):
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
    if status == ASSETS.ApplicationTodayStatus.ABSENT.title:
        return 9


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
            _new_app_tech, created = ApplicationTechnic.objects.get_or_create(
                technic_sheet=application_technic.technic_sheet,
                application_today=application_today
            )
            _new_app_tech.description = _new_app_tech.description + str_desc if _new_app_tech.description else str_desc
            _new_app_tech.save()

            application_technic.isChecked = True
            application_technic.id_orig_app = _new_app_tech.id
            application_technic.save()
            TECHNIC_SHEET_SERVICE.calculate_count_applications(application_technic.technic_sheet_id)

        elif application_technic.isChecked:
            _supply_at = APP_TECHNIC_SERVICE.get_app_technic(
                pk=application_technic.id_orig_app
            )
            _supply_at.description = _supply_at.description.replace(str_desc, '')
            _supply_at.save()
            if not _supply_at.description:
                _supply_at.delete()
            application_technic.isChecked = False

            application_technic.id_orig_app = None
            application_technic.save()
            TECHNIC_SHEET_SERVICE.calculate_count_applications(application_technic.technic_sheet_id)


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
    return _technic_sheet.order_by('technic__title', 'driver_sheet__driver__last_name')


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

    color_title = request.POST.get('color_title')
    color_title = color_title if color_title is not None else '#000000'

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
        if color_title:
            _user.color_title = color_title
        _user.filter_technic = filter_technic
        _user.sort_by = sort_by
        _user.save()


def prepare_data_for_filter(context: dict) -> dict:
    """
    Подготовка и получения данных для фильтра
    :param context:
    :return:
    """
    foreman_list = USERS_SERVICE.get_user_queryset(post=ASSETS.UserPosts.FOREMAN.title).values(
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


def send_messages_by_telegram(chat_id, messages):
    """
    Отправка messages пользователю с chat_id через Telegram
    :param chat_id:
    :param messages:
    :return:
    """
    if USE_TELEGRAM:
        try:
            T.BOT.send_message(chat_id=chat_id, text=messages, parse_mode='html')
        except T.ApiTelegramException as e:
            log.error('send_messages_by_telegram(): ApiTelegramException')


def get_user_key(user_id) -> str:
    """
    Получить уникальный ключ для привязки Telegram
    :param user_id:
    :return:
    """
    _user = USERS_SERVICE.get_user(pk=user_id)
    if _user:
        _key = random.randint(100, 999)
        return f'{_key}{_user.id}'


def send_application_by_telegram_for_driver(current_day: WorkDaySheet, messages=None, application_today_id=None):
    all_already_send = current_day.is_all_application_send
    template_date = f'{ASSETS.WEEKDAY[current_day.date.weekday()]}, {current_day.date.day} {ASSETS.MONTHS[current_day.date.month - 1]}'
    driver_list = TECHNIC_SHEET_SERVICE.get_technic_sheet_queryset(
        date=current_day,
        status=True,
        driver_sheet__status=True,
        isArchive=False
    )
    if application_today_id:
        application_today = APP_TODAY_SERVICE.get_apps_today_queryset(pk=application_today_id)
    else:
        application_today = APP_TODAY_SERVICE.get_apps_today_queryset(
            isArchive=False,
            date=current_day,
            status=ASSETS.ApplicationTodayStatus.SEND.title)

    application_technic_list = APP_TECHNIC_SERVICE.get_apps_technic_queryset(
        select_related=('technic_sheet', 'application_today__construction_site__foreman'),
        isArchive=False,
        is_cancelled=False,
        isChecked=False,
        application_today__in=application_today
    )

    driver_sheet_list = driver_list.filter(
        id__in=application_technic_list.values_list('technic_sheet_id', flat=True)).values(
        'id',
        'driver_sheet__driver__telegram_id_chat',
        'driver_sheet__driver__last_name',
        'driver_sheet__driver__first_name',
    )

    for driver_sheet_item in driver_sheet_list:
        driver_sheet_item['applications'] = application_technic_list.filter(
            technic_sheet_id=driver_sheet_item['id']).values(
            'priority',
            'application_today__construction_site__address',
            'application_today__construction_site__foreman__last_name',
            'application_today__is_application_send',
            'description'
        ).order_by('priority')

    if all_already_send:
        msg = f'Обновленная заявка на:\n{template_date}\n\n'
    else:
        msg = f'Заявка на:\n{template_date}\n\n'

    for item in driver_sheet_list:
        msg = f"{item['driver_sheet__driver__last_name']} {item['driver_sheet__driver__first_name']}\n{msg}"
        for app in item['applications']:
            if app['application_today__construction_site__foreman__last_name']:
                msg += f"{app['priority']}) {app['application_today__construction_site__address']} ({app['application_today__construction_site__foreman__last_name']})\n"
            else:
                msg += f"{app['priority']}) {app['application_today__construction_site__address']}\n"
            if app['description']:
                msg += f"{app['description']}\n\n"
            else:
                msg += f"\n"
        if item['driver_sheet__driver__telegram_id_chat']:
            send_messages_by_telegram(chat_id=item['driver_sheet__driver__telegram_id_chat'], messages=msg)


def send_application_by_telegram_for_foreman(current_day: WorkDaySheet, messages=None, application_today_id=None):
    all_already_send = current_day.is_all_application_send
    template_date = f'{ASSETS.WEEKDAY[current_day.date.weekday()]}, {current_day.date.day} {ASSETS.MONTHS[current_day.date.month - 1]}'
    foreman_list = USERS_SERVICE.get_user_queryset(
        isArchive=False,
        post__in=(ASSETS.UserPosts.FOREMAN.title, ASSETS.UserPosts.MASTER.title, ASSETS.UserPosts.SUPPLY.title)
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
            isArchive=False, date=current_day, status=ASSETS.ApplicationTodayStatus.SEND.title)

    for item in foreman_list:
        if item['post'] == ASSETS.UserPosts.FOREMAN.title:
            foreman_id = item['id']
        else:
            foreman_id = item['supervisor_user_id']
        if foreman_id:
            app_today = application_today.filter(construction_site__foreman_id=foreman_id)
        else:
            app_today = application_today.filter(construction_site__address=ASSETS.MessagesAssets.CS_SUPPLY_TITLE.value)
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
    administrators_list = USERS_SERVICE.get_user_queryset(isArchive=False, post=ASSETS.UserPosts.ADMINISTRATOR.title)

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


def copy_application_to_target_day(id_application_today,
                                   _target_day: date,
                                   default_status: str = ASSETS.ApplicationTodayStatus.SAVED.title):
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
    """
    Отправить technic_sheet в спец. объект и назначить спец. задание по умолчанию
    :param technic_sheet_id:
    :return:
    """
    construction_site, _ = ConstructionSite.objects.get_or_create(address=ASSETS.MessagesAssets.CS_SPEC_TITLE.value)

    technic_sheet = TECHNIC_SHEET_SERVICE.get_technic_sheet(pk=technic_sheet_id)
    current_day = technic_sheet.date
    application_today, _ = ApplicationToday.objects.get_or_create(
        construction_site=construction_site,
        date=current_day)

    application_technic, at_created = ApplicationTechnic.objects.get_or_create(
        application_today=application_today,
        technic_sheet=technic_sheet)
    if at_created:
        technic_sheet.increment_count_application()

    template_description = TECHNIC_SERVICE.get_description_mode_for_spec_app(technic_sheet.technic.id)
    match template_description:
        case ASSETS.TaskDescriptionMode.DEFAULT:
            description = PARAMETER_SERVICE.get_parameter(
                name=VAR.VAR_TASK_DESCRIPTION_FOR_SPEC_CONSTR_SITE['name']
            ).value
        case ASSETS.TaskDescriptionMode.MANUAL:
            description = TECHNIC_SERVICE.get_task_description(
                technic__id=technic_sheet.technic.id).description
        case ASSETS.TaskDescriptionMode.AUTO:
            task_description = APP_TECHNIC_SERVICE.get_apps_technic_queryset(
                application_today__construction_site__address=ASSETS.MessagesAssets.CS_SPEC_TITLE.value,
                application_today__date__date=current_day.date - timedelta(days=1),
                technic_sheet__technic=technic_sheet.technic,
            )
            if task_description.exists():
                description = task_description.first().description
            else:
                description = ''
        case _:
            description=''

    application_technic.description = description
    application_technic.save()
    application_today.status = ASSETS.ApplicationTodayStatus.SUBMITTED.title
    application_today.save(update_fields=['status'])


def get_view_mode(_date: date) -> str:
    """
    Получить режим отображения
    :param _date:
    :return:
    """
    if _date == TODAY:
        return ASSETS.ViewMode.CURRENT.value
    elif _date < TODAY:
        return ASSETS.ViewMode.ARCHIVE.value
    elif _date > TODAY:
        return ASSETS.ViewMode.FUTURE.value
    else:
        return 'None'


def get_accept_mode(workday: WorkDaySheet) -> bool:
    """
    Получить режим accept mode
    True - заявки принимаются
    False - заявки не принимаются
    :param workday:
    :return:
    """

    var_time_recept_apps = PARAMETER_SERVICE.get_parameter(
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


def set_accept_mode(current_day: WorkDaySheet, mode: ASSETS.AcceptMode):
    """
    Установить режим accept mode
    :param current_day:
    :param mode:
    :return:
    """
    current_day.accept_mode = mode.value
    current_day.save(update_fields=['accept_mode'])


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


def change_up_status_for_application_today(workday: WorkDaySheet, application_today_id=None,
                                           current_status=None) -> str:
    """
    Изменить статус заявки на следующий статус
    :param workday:
    :param application_today_id:
    :param current_status:
    :return:
    """
    if application_today_id:
        application_today = APP_TODAY_SERVICE.get_apps_today(pk=application_today_id)
        application_today.set_next_status()
        return application_today.status
    else:
        application_today_list = APP_TODAY_SERVICE.get_apps_today_queryset(
            isArchive=False,
            date=workday,
            status=current_status
        )
        [application_today.set_next_status() for application_today in application_today_list]
        return application_today_list.first().status


def get_status_lists_of_apps_today(applications_today: QuerySet[ApplicationToday]) -> dict:
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

    apps_today = applications_today.values('id', 'status')
    for app in apps_today:
        if app['status'] == ASSETS.ApplicationTodayStatus.ABSENT.title:
            status_lists[ASSETS.ApplicationTodayStatus.ABSENT.title].append(app['id'])
        elif app['status'] == ASSETS.ApplicationTodayStatus.SAVED.title:
            status_lists[ASSETS.ApplicationTodayStatus.SAVED.title].append(app['id'])
        elif app['status'] == ASSETS.ApplicationTodayStatus.SUBMITTED.title:
            status_lists[ASSETS.ApplicationTodayStatus.SUBMITTED.title].append(app['id'])
        elif app['status'] == ASSETS.ApplicationTodayStatus.APPROVED.title:
            status_lists[ASSETS.ApplicationTodayStatus.APPROVED.title].append(app['id'])
        elif app['status'] == ASSETS.ApplicationTodayStatus.SEND.title:
            status_lists[ASSETS.ApplicationTodayStatus.SEND.title].append(app['id'])
    return status_lists


def prepare_global_parameters():
    """
    Авто создание переменных
    :return:
    """
    parameters_list = VAR.VARIABLES_LIST
    PARAMETER_SERVICE.create_global_parameters(global_parameters=parameters_list)


def get_accept_to_change_materials_app(current_workday: WorkDaySheet) -> bool:
    """
    Разрешено ли редактировать заявки на материалы
    :param current_workday:
    :return:
    """
    is_accept = False
    var_time_limit = PARAMETER_SERVICE.get_parameter(
        name=VAR.VAR_TIME_RECEPTION_OF_MATERIALS['name']
    )
    if not var_time_limit:
        log.warning(
            f"Переменная {VAR.VAR_TIME_RECEPTION_OF_MATERIALS['name']} \
            для ограничения времени подачи заявок на материалы не существует.")
        return False

    time_limit = var_time_limit.time
    next_workday = WORK_DAY_SERVICE.get_next_workday()

    if (current_workday == next_workday
            and NOW < time_limit):
        is_accept = True
        log.debug(f"get_accept_to_change_materials_app(): C1")

    elif TODAY.weekday() in (4,) and current_workday.date.weekday() in (0,) and NOW < time_limit:
        is_accept = True
        log.debug(f"get_accept_to_change_materials_app(): C2")

    elif current_workday.date > next_workday.date:
        is_accept = True
        log.debug(f"get_accept_to_change_materials_app(): C3")

    return is_accept


def validate_telephone(telephone: str, length=9, use_pref=True) -> str | None:
    """
    Валидация номера телефона
    :param use_pref:
    :param length:
    :param telephone:
    :return:
    """
    if telephone:
        pref = '+375'
        out = [sym for sym in telephone if sym in '0123456789']
        out = ''.join(out)

        if len(out) >= length:
            if use_pref:
                return pref + out[-length:]
            else:
                return out[-length:]
        else:
            return None
