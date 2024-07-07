from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse

from dashboard.models import User
from django.contrib.auth import login, logout, authenticate
# from dashboard.models import Administrator, Foreman, Master, Mechanic, Driver, Supply, Employee
from dashboard.models import Technic
from dashboard.models import ConstructionSite
from dashboard.models import WorkDaySheet, DriverSheet, TechnicSheet
from dashboard.models import ApplicationToday, ApplicationTechnic, ApplicationMaterial
from dashboard.models import Parameter  # , Telebot

import dashboard.assets as ASSETS
import config.endpoints as ENDPOINTS
import dashboard.utilities as U
import dashboard.variables as VAR
# import dashboard.telegram_bot as T

#   SERVICE--------------------------------------------------
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
import dashboard.services.add_edit_application as ADD_EDIT_APP_SERVICE
import dashboard.services.parametr as PARAMETER_SERVICE
#   SERVICE--------------------------------------------------

from logger import getLogger

log = getLogger(__name__)


# Create your views here.


def dashboard_view(request):
    if request.user.is_anonymous:
        return HttpResponseRedirect(ENDPOINTS.LOGIN)

    current_day = WORK_DAY_SERVICE.get_current_day(request)

    context = {
        'title': request.user,
        'current_day': current_day,
        'ONLY_READ': current_day.is_only_read,
        'APPLICATION_STATUS': ASSETS.APPLICATION_STATUS_dict
    }
    context = U.get_prepared_data(context, current_day)
    context = U.prepare_data_for_filter(context)

    if not current_day.status:
        if (request.GET.get('current_day') is None or request.GET.get('current_day') == '' or
                USERS_SERVICE.is_driver(request.user) or
                USERS_SERVICE.is_employee(request.user)):
            next_workday = WORK_DAY_SERVICE.get_next_workday(current_day.date)
            return HttpResponseRedirect(ENDPOINTS.DASHBOARD + f'?current_day={next_workday.date}')

        return render(request, 'content/spec/weekend.html', context)

    status_list_application_today = APP_TODAY_SERVICE.get_status_lists_of_apps_today(workday=current_day)
    context['status_list_application_today'] = status_list_application_today

    #   POST    ===================================================================================================
    if request.method == 'POST':
        operation = request.POST.get('operation')
        if U.is_valid_get_request(operation) and operation == 'set_props_for_view':
            U.set_data_for_filter(request)

        if request.POST.get('operation') == 'copy':
            target_day = request.POST.get('target_day')
            application_id = request.POST.get('application_id')
            if U.is_valid_get_request(target_day) and U.is_valid_get_request(application_id):
                default_app_status = APP_TODAY_SERVICE.get_default_status_for_apps_today(request.user)
                U.copy_application_to_target_day(application_id, target_day, default_app_status)
    #   POST    ===================================================================================================

    #   get dashboard for administrator -----------------------------------------------------------------------
    if USERS_SERVICE.is_administrator(request.user):
        context = DASHBOARD_SERVICE.get_dashboard_for_admin(request=request, current_day=current_day, context=context)
        return render(request, 'content/dashboard/admin_dashboard.html', context)
    #   -------------------------------------------------------------------------------------------------------

    #   get dashboard for foreman or master -------------------------------------------------------------------
    elif USERS_SERVICE.is_foreman(request.user) or USERS_SERVICE.is_master(request.user):

        foreman = USERS_SERVICE.get_foreman(request.user)
        if not foreman:
            return HttpResponseRedirect(ENDPOINTS.LOGIN)

        context = DASHBOARD_SERVICE.get_dashboard_for_foreman_or_master(
            request=request, foreman=foreman, current_day=current_day, context=context)
        return render(request, 'content/dashboard/foreman_dashboard.html', context)
    #   -------------------------------------------------------------------------------------------------------

    #   get dashboard for mechanic ----------------------------------------------------------------------------
    elif USERS_SERVICE.is_mechanic(request.user):
        context = DASHBOARD_SERVICE.get_dashboard_for_mechanic(
            request=request, current_day=current_day, context=context)
        return render(request, 'content/dashboard/mechanic_dashboard.html', context)
    #   -------------------------------------------------------------------------------------------------------

    #   get dashboard for supply ------------------------------------------------------------------------------
    elif USERS_SERVICE.is_supply(request.user):
        context = DASHBOARD_SERVICE.get_dashboard_for_supply(request=request, current_day=current_day, context=context)
        return render(request, 'content/dashboard/supply_dashboard.html', context)
    #   -------------------------------------------------------------------------------------------------------

    #   get dashboard for employee ----------------------------------------------------------------------------
    elif USERS_SERVICE.is_employee(request.user):
        context = DASHBOARD_SERVICE.get_dashboard_for_employee(
            request=request, current_day=current_day, context=context)
        return render(request, 'content/dashboard/employee_dashboard.html', context)
    #   -------------------------------------------------------------------------------------------------------

    #   get dashboard for driver ------------------------------------------------------------------------------
    elif USERS_SERVICE.is_driver(request.user):
        context = DASHBOARD_SERVICE.get_dashboard_for_driver(request=request, current_day=current_day, context=context)
        return render(request, 'content/dashboard/driver_dashboard.html', context)
    #   -------------------------------------------------------------------------------------------------------

    else:
        return HttpResponseRedirect(ENDPOINTS.LOGIN)


def clear_application_today(request):
    if request.user.is_authenticated:
        if any((
                USERS_SERVICE.is_administrator(request.user),
                USERS_SERVICE.is_foreman(request.user),
                USERS_SERVICE.is_master(request.user),
                USERS_SERVICE.is_supply(request.user)
        )):
            foreman = USERS_SERVICE.get_foreman(request.user)
            app_today_id = request.GET.get('app_today_id')
            if app_today_id:
                application_today = APP_TODAY_SERVICE.get_apps_today(pk=app_today_id)
                if not application_today:
                    return HttpResponseRedirect(ENDPOINTS.DASHBOARD)

                if (not USERS_SERVICE.is_administrator(request.user) and
                        foreman != application_today.construction_site.foreman):
                    return HttpResponseRedirect(ENDPOINTS.DASHBOARD)

                elif USERS_SERVICE.is_supply(request.user):
                    supply_technic_list = TECHNIC_SERVICE.get_supply_technic_list()
                    app_technic_list = APP_TECHNIC_SERVICE.get_apps_technic_queryset(
                        application_today__date=application_today.date,
                        isArchive=False,
                        technic_sheet__technic__in=supply_technic_list
                    ).exclude(application_today=application_today)
                    app_technic_list.update(isChecked=False)
                APP_TODAY_SERVICE.delete_application_today(application_today)

            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        else:
            return HttpResponseRedirect(ENDPOINTS.DASHBOARD)
    return HttpResponseRedirect(ENDPOINTS.LOGIN)


def validate_application_today_view(request):
    if request.user.is_authenticated:
        app_today_id = request.GET.get('app_today_id')
        current_day = request.GET.get('current_day')
        default_status = APP_TODAY_SERVICE.get_default_status_for_apps_today(request.user)
        application_today = APP_TODAY_SERVICE.get_apps_today(pk=app_today_id)

        if application_today:
            APP_TODAY_SERVICE.validate_application_today(
                application_today=application_today,
                default_status=default_status)
        return HttpResponseRedirect(f'{ENDPOINTS.DASHBOARD}?current_day={current_day}')
    else:
        return HttpResponseRedirect(ENDPOINTS.LOGIN)


def edit_application_view(request):
    if request.user.is_authenticated:
        context = {'title': 'Создать заявку'}
        current_day = WORK_DAY_SERVICE.get_current_day(request)
        context['current_day'] = current_day
        context['weekday'] = ASSETS.WEEKDAY[current_day.date.weekday()]

        if not current_day.status:
            return render(request, 'content/spec/weekend.html', context)

        context['technics'] = TECHNIC_SERVICE.get_technics_queryset(
            isArchive=False
        ).distinct().values_list('title', flat=True)

        technic_sheets = TECHNIC_SHEET_SERVICE.get_technic_sheet_queryset(
            select_related=('technic', 'driver_sheet__driver'),
            isArchive=False,
            status=True,
            driver_sheet__isnull=False,
            driver_sheet__status=True,
            date=current_day
        )

        if not technic_sheets.exists():
            U.prepare_sheets(current_day)

        technic_titles_dict = TECHNIC_SERVICE.get_dict_short_technic_names(technic_sheets=technic_sheets)
        context['technic_titles_dict'] = technic_titles_dict

        context['technic_driver_list'] = ADD_EDIT_APP_SERVICE.get_technic_driver_list(
            technic_titles=technic_titles_dict,
            technic_sheets=technic_sheets
        )

        if request.method == 'POST':
            operation = request.POST.get('operation')  # операция
            post_application_today_id = request.POST.get('app_today_id')
            post_current_day = request.POST.get('current_day')
            post_construction_site_id = request.POST.get('construction_site_id')  # id construction_site
            post_technic_title_shrt = request.POST.get('technic_title_shrt')
            post_technic_sheet_id = request.POST.get('technic_sheet_id')
            post_application_technic_description = request.POST.get('app_tech_desc')
            post_application_technic_id = request.POST.get('application_technic_id')
            post_application_today_description = request.POST.get('application_today_description')
            post_application_material_id = request.POST.get('app_material_id')
            post_application_material_description = request.POST.get('material_description')

            if operation == 'add_technic_to_application':
                log.info('add_technic_to_application')
                if (U.is_valid_get_request(post_application_today_id) and
                        U.is_valid_get_request(post_technic_title_shrt)):
                    if not U.is_valid_get_request(post_technic_sheet_id):
                        technic_title = technic_titles_dict.get(post_technic_title_shrt)
                        some_technic_sheet = TECHNIC_SHEET_SERVICE.get_some_technic_sheet(
                            technic_title=technic_title, workday=current_day
                        )
                    else:
                        some_technic_sheet = TECHNIC_SHEET_SERVICE.get_technic_sheet(pk=post_technic_sheet_id)
                    description = post_application_technic_description if post_application_technic_description else ''
                    APP_TECHNIC_SERVICE.create_app_technic(
                        application_today_id=post_application_today_id,
                        technic_sheet=some_technic_sheet,
                        description=description
                    )
                    some_technic_sheet.increment_count_application()

            elif operation == 'reject_application_technic':
                log.info('reject_application_technic')
                if (U.is_valid_get_request(post_application_today_id) and
                        U.is_valid_get_request(post_application_technic_id)):
                    APP_TECHNIC_SERVICE.reject_or_accept_apps_technic(app_tech_id=post_application_technic_id)

            elif operation == 'apply_changes_application_technic':
                log.info('apply_changes_application_technic')
                if (U.is_valid_get_request(post_application_technic_id) and
                        U.is_valid_get_request(post_technic_title_shrt)):

                    application_technic = APP_TECHNIC_SERVICE.get_app_technic(pk=post_application_technic_id)

                    if not U.is_valid_get_request(post_technic_sheet_id):
                        technic_title = technic_titles_dict.get(post_technic_title_shrt)
                        some_technic_sheet = TECHNIC_SHEET_SERVICE.get_some_technic_sheet(
                            technic_title=technic_title, workday=current_day
                        )
                    else:
                        some_technic_sheet = TECHNIC_SHEET_SERVICE.get_technic_sheet(pk=post_technic_sheet_id)
                    description = post_application_technic_description if post_application_technic_description else ''
                    if application_technic.technic_sheet.id != some_technic_sheet.id:
                        application_technic.technic_sheet.decrement_count_application()
                        application_technic.technic_sheet = some_technic_sheet
                        some_technic_sheet.increment_count_application()
                    application_technic.description = description
                    application_technic.save(update_fields=['technic_sheet', 'description'])


            elif operation == 'save_application_description':
                if U.is_valid_get_request(post_application_today_id):
                    application_today = APP_TODAY_SERVICE.get_apps_today(pk=post_application_today_id)
                    if U.is_valid_get_request(post_application_today_description):
                        application_today.description = post_application_today_description
                    else:
                        application_today.description = None
                    application_today.save(update_fields=['description'])

            elif operation == 'save_application_materials':
                log.info('save_application_materials')
                if U.is_valid_get_request(post_application_material_id) and post_application_material_description == '':
                    APP_MATERIAL_SERVICE.get_app_material(pk=post_application_material_id).delete()
                elif not U.is_valid_get_request(post_application_material_id) and U.is_valid_get_request(
                        post_application_material_description) and U.is_valid_get_request(post_application_today_id):
                    APP_MATERIAL_SERVICE.create_app_material(
                        application_today_id=post_application_today_id,
                        description=post_application_material_description
                    )
                elif U.is_valid_get_request(post_application_material_id) and U.is_valid_get_request(
                        post_application_material_description):
                    application_material = APP_MATERIAL_SERVICE.get_app_material(pk=post_application_material_id)
                    application_material.description = post_application_material_description
                    application_material.save(update_fields=['description'])

            return HttpResponseRedirect(ENDPOINTS.DASHBOARD)

        #   method GET --------------------------------------------------------------------------------------
        constr_site_id = request.GET.get('constr_site_id')
        if U.is_valid_get_request(constr_site_id):
            construction_site = CONSTR_SITE_SERVICE.get_construction_sites(pk=constr_site_id)
            if construction_site:
                context['construction_site'] = construction_site
            else:
                return HttpResponseRedirect(ENDPOINTS.DASHBOARD)

            application_today = APP_TODAY_SERVICE.get_apps_today(
                construction_site=construction_site,
                date=current_day,
                isArchive=False
            )
            if not application_today:
                default_status = APP_TODAY_SERVICE.get_default_status_for_apps_today(request.user)
                application_today = APP_TODAY_SERVICE.create_app_today(
                    construction_site=construction_site,
                    date=current_day,
                    status=default_status
                )

            if application_today:
                context['application_today'] = {
                    'id': application_today.id,
                    'date__date': application_today.date,
                    'status': application_today.status,
                    'description': application_today.description
                }
                context['application_today']['application_technic'] = APP_TECHNIC_SERVICE.get_apps_technic_queryset(
                    isArchive=False,
                    application_today=application_today).values(
                    'id',
                    'technic_sheet_id',
                    'technic_sheet__technic__title',
                    'technic_sheet__driver_sheet__driver__last_name',
                    'technic_sheet__driver_sheet__driver__first_name',
                    'is_cancelled',
                    'description'
                )
                context['application_today']['application_material'] = APP_MATERIAL_SERVICE.get_apps_material_queryset(
                    isArchive=False,
                    application_today=application_today).values(
                    'id',
                    'description',
                    'isChecked',
                    'is_cancelled'
                ).first()

        return render(request, 'content/dashboard/edit_application.html', context)
    return HttpResponseRedirect(ENDPOINTS.LOGIN)


def login_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect(ENDPOINTS.DASHBOARD)
    if request.method == 'GET':
        return render(request, 'content/login.html')
    if request.method == 'POST':
        username = request.POST.get('username')
        username = username.strip()
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is None:
            username = username.capitalize()
            user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(ENDPOINTS.DASHBOARD)  # TODO: redirect to Home page
        else:
            return render(request, 'content/login.html', {'error': ASSETS.ERROR_MESSAGES['login']})
    return HttpResponse(status=403)


def restore_password_view(request):
    context = {}
    if request.method == 'POST':
        _last_name = request.POST.get('last_name')
        last_name = _last_name.strip().lower().capitalize()
        _user = USERS_SERVICE.get_user_queryset(
            isArchive=False,
            last_name=last_name,
        )
        if _user.exists():
            context['users_list'] = _user
        else:
            context['msg'] = 'Данный пользователь не найден'
    user_id = request.GET.get('user_id')
    if U.is_valid_get_request(user_id):
        restore_user = USERS_SERVICE.get_user(pk=user_id)
        if restore_user:
            default_passwd = PARAMETER_SERVICE.get_parameter(name=VAR.VAR_DEFAULT_PASSWORD['name'])
            if default_passwd:
                restore_user.set_password(default_passwd.value)
                restore_user.save(update_fields=['password'])
                context['msg_success'] = {'login': restore_user.username, 'password': default_passwd.value}
            else:
                log.error("Ошибка с параметром 'default_passwd'")
                context['msg'] = 'Произошла какая-то ошибка'
        else:
            log.error("restore_password_view(): restore_user не найден")
    return render(request, 'content/spec/restore_password.html', context)


def logout_view(request):
    if request.user.is_authenticated:
        logout(request)
    return HttpResponseRedirect(ENDPOINTS.LOGIN)


def register_view(request):
    context = {
        'user_posts': {
            ASSETS.EMPLOYEE: ASSETS.USER_POSTS_dict[ASSETS.EMPLOYEE],
            ASSETS.DRIVER: ASSETS.USER_POSTS_dict[ASSETS.DRIVER],
        }
    }

    if request.method == 'GET':
        return render(request, 'content/register.html', context)
    if request.method == 'POST':
        new_user = USERS_SERVICE.add_or_edit_user(request.POST, user_id=None)
        if new_user is not None and request.user.is_anonymous:
            login(request, new_user)
            return HttpResponseRedirect(ENDPOINTS.DASHBOARD)
        elif new_user is not None and request.user.is_authenticated:
            return HttpResponseRedirect('/')  # TODO redirect if create new user
        else:
            context['error'] = ASSETS.ERROR_MESSAGES['register']
            return render(request, 'content/register.html', context)

    return HttpResponse(status=403)


#   Sheets--------------------------------------------------------------------------------------------------------------
def workday_sheet_view(request):
    if request.user.is_authenticated:
        context = {'title': 'Рабочие дни'}

        if request.method == 'POST':
            day_id = request.POST.get('item_id')
            if U.is_valid_get_request(day_id):
                WORK_DAY_SERVICE.change_status(work_day_id=day_id)
        current_day = WORK_DAY_SERVICE.get_current_day(request)
        context = U.get_prepared_data(context=context, current_workday=current_day)
        current_date = current_day.date
        workdays = WORK_DAY_SERVICE.get_range_workdays(start_date=current_date, before_days=3, after_days=7).values()

        for day in workdays:
            day['weekday'] = ASSETS.WEEKDAY[day['date'].weekday()]
        context['workdays'] = workdays
        return render(request, 'content/sheet/workday_sheet.html', context)
    return HttpResponseRedirect(ENDPOINTS.LOGIN)


def driver_sheet_view(request):
    if request.user.is_authenticated:
        context = {'title': 'Табель: водители'}

        if request.method == "POST":
            driver_sheet_id = request.POST.get('item_id')
            if driver_sheet_id is not None and driver_sheet_id != '':
                DRIVER_SHEET_SERVICE.change_status(driver_sheet_id=driver_sheet_id)

        current_day = WORK_DAY_SERVICE.get_current_day(request)
        context = U.get_prepared_data(context, current_day)

        if current_day.date >= U.TODAY and current_day.status:
            DRIVER_SHEET_SERVICE.prepare_driver_sheet(current_day)

        driver_sheet = DRIVER_SHEET_SERVICE.get_driver_sheet_queryset(
            select_related=('driver',),
            order_by=('driver__last_name',),
            date=current_day,
        )

        context['driver_sheets'] = driver_sheet
        context['current_day'] = current_day

        return render(request, 'content/sheet/driver_sheet.html', context)
    return HttpResponseRedirect(ENDPOINTS.LOGIN)


def technic_sheet_view(request):
    if request.user.is_authenticated:
        context = {'title': 'Табель: техника'}

        if request.method == 'POST':
            technic_sheet_id = request.POST.get('item_id')
            if technic_sheet_id:
                TECHNIC_SHEET_SERVICE.change_status(technic_sheet_id=technic_sheet_id)

            technic_sheet_id = request.POST.get('technic_sheet_id')
            driver_sheet_id = request.POST.get('driver_sheet_id')
            if technic_sheet_id:
                TECHNIC_SHEET_SERVICE.change_driver(
                    technic_sheet_id=technic_sheet_id,
                    driver_sheet_id=driver_sheet_id)

        current_day = WORK_DAY_SERVICE.get_current_day(request)
        context['current_day'] = current_day
        context = U.get_prepared_data(context, current_day)

        if current_day.date >= U.TODAY and current_day.status:
            DRIVER_SHEET_SERVICE.prepare_driver_sheet(workday=current_day)
            TECHNIC_SHEET_SERVICE.prepare_technic_sheets(workday=current_day)

        technic_sheet = TECHNIC_SHEET_SERVICE.get_technic_sheet_queryset(
            select_related=('driver_sheet__driver', 'technic__attached_driver'),
            order_by=('technic__title',),
            date=current_day,
        )
        driver_sheet = DRIVER_SHEET_SERVICE.get_driver_sheet_queryset(
            select_related=('driver',),
            date=current_day
        )

        context['technic_sheets'] = technic_sheet
        context['driver_sheets'] = driver_sheet

        return render(request, 'content/sheet/technic_sheet.html', context)
    return HttpResponseRedirect(ENDPOINTS.LOGIN)


#   --------------------------------------------------------------------------------------------------------------------


#   Technic-------------------------------------------------------------------------------------------------------------
def technic_view(request):
    if request.user.is_authenticated:
        context = {'title': 'Техника'}
        technics = TECHNIC_SERVICE.get_technics_queryset(
            select_related=('attached_driver',),
            order_by=('title',),
            isArchive=False
        )
        context['technics'] = technics
        return render(request, 'content/technic/technics.html', context)
    return HttpResponseRedirect(ENDPOINTS.LOGIN)


def edit_technic_view(request):
    if request.user.is_authenticated:
        context = {'title': 'Добавить технику'}

        technic_id = request.GET.get('tech_id')
        context['drivers'] = USERS_SERVICE.get_user_queryset(post=ASSETS.DRIVER)
        context['supervisors'] = dict(
            [(key, value) for key, value in ASSETS.USER_POSTS_dict.items() if key in (ASSETS.MECHANIC, ASSETS.SUPPLY)])
        technic_type_list = set(Technic.objects.filter().values_list('type', flat=True))
        context['technic_type_list'] = sorted(technic_type_list)

        if technic_id:
            technic = TECHNIC_SERVICE.get_technic(pk=technic_id)
            if technic:
                context['technic'] = technic
                context['title'] = 'Редактировать технику'
            else:
                return HttpResponseRedirect(ENDPOINTS.TECHNICS)

        if request.method == 'POST':
            data = request.POST
            TECHNIC_SERVICE.add_or_edit_technic(data, technic_id)
            return HttpResponseRedirect(ENDPOINTS.TECHNICS)

        return render(request, 'content/technic/edit_technic.html', context)
    return HttpResponseRedirect(ENDPOINTS.LOGIN)


def delete_technic_view(request):
    if request.user.is_authenticated:
        if USERS_SERVICE.is_administrator(request.user) or USERS_SERVICE.is_mechanic(request.user):
            technic_id = request.GET.get('tech_id')
            if technic_id:
                technic = TECHNIC_SERVICE.delete_technic(technic_id)
                if technic:

                    _technic_sheet = TECHNIC_SHEET_SERVICE.get_technic_sheet_queryset(
                        technic=technic, date__date__gte=U.TODAY
                    )

                    _application_technic = APP_TECHNIC_SERVICE.get_apps_technic_queryset(
                        technic_sheet__in=_technic_sheet
                    )
                    _application_today = APP_TODAY_SERVICE.get_apps_today_queryset(
                        date__date__gte=U.TODAY
                    )

                    _application_technic.delete()
                    _technic_sheet.delete()

                    for _app_today in _application_today:
                        APP_TODAY_SERVICE.validate_application_today(application_today=_app_today)
                        # U.check_application_today(_app_today)
        return HttpResponseRedirect(ENDPOINTS.TECHNICS)
    return HttpResponseRedirect(ENDPOINTS.LOGIN)


#   --------------------------------------------------------------------------------------------------------------------


#   User----------------------------------------------------------------------------------------------------------------
def users_view(request):
    if request.user.is_authenticated:
        context = {
            'title': 'Все пользователи',
            'users_list': [],
            'user_post': ASSETS.USER_POSTS_dict
        }
        if USERS_SERVICE.is_administrator(request.user):
            users_list = USERS_SERVICE.get_user_queryset(order_by=('last_name',))
        elif USERS_SERVICE.is_master(request.user) or USERS_SERVICE.is_foreman(request.user):
            users_list = USERS_SERVICE.get_user_queryset(order_by=('last_name',)).exclude(post=ASSETS.ADMINISTRATOR)
        elif USERS_SERVICE.is_mechanic(request.user):
            users_list = USERS_SERVICE.get_user_queryset(post=ASSETS.DRIVER, order_by=('last_name',))
        else:
            users_list = []
        context['users_list'] = users_list
        return render(request, 'content/users/users.html', context)

    return HttpResponseRedirect(ENDPOINTS.LOGIN)


def edit_user_view(request):
    if request.user.is_authenticated:
        context = {'title': 'Добавить пользователя',
                   'posts': ASSETS.USER_POSTS_dict,
                   'foreman_list': USERS_SERVICE.get_user_queryset(post=ASSETS.FOREMAN)
                   }
        if USERS_SERVICE.is_mechanic(request.user):
            context['posts'] = {ASSETS.DRIVER: ASSETS.USER_POSTS_dict[ASSETS.DRIVER]}
        if USERS_SERVICE.is_master(request.user) or USERS_SERVICE.is_foreman(request.user):
            context['posts'] = {ASSETS.EMPLOYEE: ASSETS.USER_POSTS_dict[ASSETS.EMPLOYEE]}

        user_id = request.GET.get('user_id')
        if U.is_valid_get_request(user_id):
            user_ = USERS_SERVICE.get_user(pk=user_id)
            if user_:
                context['user_list'] = user_
                context['title'] = 'Изменить пользователя'
            else:
                return HttpResponseRedirect(ENDPOINTS.USERS)

        if request.method == 'POST':
            _user = USERS_SERVICE.add_or_edit_user(request.POST, user_id)
            return HttpResponseRedirect(ENDPOINTS.USERS)

        return render(request, 'content/users/edit_user.html', context)
    return HttpResponseRedirect(ENDPOINTS.LOGIN)


def delete_user_view(request):
    if request.user.is_authenticated:
        if USERS_SERVICE.is_administrator(request.user):
            user_id = request.GET.get('user_id')
            if U.is_valid_get_request(user_id):
                _user = USERS_SERVICE.delete_user(user_id)
                if _user:
                    DRIVER_SHEET_SERVICE.get_driver_sheet_queryset(driver=_user, date__date__gte=U.TODAY).delete()
    return HttpResponseRedirect(ENDPOINTS.USERS)


#   --------------------------------------------------------------------------------------------------------------------


def construction_site_view(request):
    if request.user.is_authenticated:
        context = {'title': 'Строительные объекты'}

        if USERS_SERVICE.is_administrator(request.user):
            context['construction_sites'] = CONSTR_SITE_SERVICE.get_construction_site_queryset(
                select_related=('foreman',),
                isArchive=False
            )

        if USERS_SERVICE.is_foreman(request.user):
            context['construction_sites'] = CONSTR_SITE_SERVICE.get_construction_site_queryset(
                select_related=('foreman',),
                isArchive=False,
                foreman=request.user)

        if USERS_SERVICE.is_master(request.user):
            context['construction_sites'] = CONSTR_SITE_SERVICE.get_construction_site_queryset(
                select_related=('foreman',),
                isArchive=False,
                foreman_id=request.user.supervisor_user_id)

        hide_constr_site_id = request.GET.get('hide')
        if U.is_valid_get_request(hide_constr_site_id):
            CONSTR_SITE_SERVICE.hide_construction_site(constr_site_id=hide_constr_site_id)
            return HttpResponseRedirect(ENDPOINTS.CONSTRUCTION_SITES)

        delete_constr_site_id = request.GET.get('delete')
        if U.is_valid_get_request(delete_constr_site_id):
            deleted_construction_site = CONSTR_SITE_SERVICE.delete_construction_site(
                constr_site_id=delete_constr_site_id)
            application_today = APP_TODAY_SERVICE.get_apps_today_queryset(
                construction_site=deleted_construction_site,
                date__date__gte=U.TODAY
            )
            application_technic = APP_TECHNIC_SERVICE.get_apps_technic_queryset(
                application_today__in=application_today
            )
            application_material = APP_MATERIAL_SERVICE.get_apps_material_queryset(
                application_today__in=application_today
            )
            technic_sheet_id_list = application_technic.values_list('technic_sheet', flat=True)
            TECHNIC_SHEET_SERVICE.decrement_technic_sheet_list(technic_sheet_id_list)
            application_material.delete()
            application_technic.delete()
            application_today.delete()

            return HttpResponseRedirect(ENDPOINTS.CONSTRUCTION_SITES)

        return render(request, 'content/construction_site/construction_sites.html', context)
    return HttpResponseRedirect(ENDPOINTS.LOGIN)


def edit_construction_sites(request):
    if request.user.is_authenticated:
        context = {
            'title': 'Изменить объект',
            'foreman_list': USERS_SERVICE.get_user_queryset(post=ASSETS.FOREMAN, order_by=('last_name',))
        }

        if request.method == 'POST':
            _id = request.POST.get('id')
            data = request.POST
            CONSTR_SITE_SERVICE.create_or_edit_construction_site(data, _id)
            return HttpResponseRedirect(ENDPOINTS.CONSTRUCTION_SITES)

        constr_site_id = request.GET.get('id')
        if U.is_valid_get_request(constr_site_id):
            constr_site = CONSTR_SITE_SERVICE.get_construction_sites(pk=constr_site_id)
            if constr_site:
                context['constr_site'] = constr_site
            else:
                return HttpResponseRedirect(ENDPOINTS.CONSTRUCTION_SITES)

        return render(request, 'content/construction_site/edit_construction_site.html', context)
    return HttpResponseRedirect(ENDPOINTS.LOGIN)


def change_status_application_today(request):
    if request.user.is_authenticated:
        application_today_id = request.GET.get('application_today_id')
        current_day = request.GET.get('current_day')
        current_status = request.GET.get('current_status')

        workday = WORK_DAY_SERVICE.get_current_day(request)

        if U.is_valid_get_request(application_today_id):
            up_level_status = U.change_up_status_for_application_today(
                workday=workday,
                application_today_id=application_today_id)
            if up_level_status == ASSETS.SEND:
                U.send_application_by_telegram_for_all(current_day=workday, application_today_id=application_today_id)
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

        elif U.is_valid_get_request(current_day) and U.is_valid_get_request(current_status):
            up_level_status = U.change_up_status_for_application_today(workday=workday, current_status=current_status)
            if up_level_status == ASSETS.SEND:
                U.send_application_by_telegram_for_all(workday)

            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    else:
        return HttpResponseRedirect(ENDPOINTS.LOGIN)


def change_weekend_to_workday(request):
    """
    Изменения выходного дня на рабочий
    :param request:
    :return:
    """
    if request.user.is_authenticated:
        _workday = request.GET.get('current_day')
        if U.is_valid_get_request(_workday):
            workday = WORK_DAY_SERVICE.get_workday(_date=_workday)
            if not workday.status:
                workday.status = True
                workday.save(update_fields=['status'])
                DRIVER_SHEET_SERVICE.prepare_driver_sheet(workday=workday)
                TECHNIC_SHEET_SERVICE.prepare_technic_sheets(workday=workday)
            return HttpResponseRedirect(f'{ENDPOINTS.DASHBOARD}?current_day={workday.date}')
    return HttpResponseRedirect(ENDPOINTS.LOGIN)


def conflicts_list_view(request):
    if request.user.is_authenticated:
        if USERS_SERVICE.is_administrator(request.user):
            context = {'title': 'Conflict List'}

            current_day = WORK_DAY_SERVICE.get_current_day(request)
            context['current_day'] = current_day

            technic_sheet_list = TECHNIC_SHEET_SERVICE.get_technic_sheet_queryset(
                date=current_day,
                driver_sheet__isnull=False,
                status=True,
                isArchive=False
            )
            priority_id_list = U.get_priority_id_list(technic_sheet_list)
            context['priority_id_list'] = priority_id_list

            busiest_technic_title_list = U.get_busiest_technic_title(technic_sheet_list)
            conflict_technic_sheet = U.get_conflict_list_of_technic_sheet(
                busiest_technic_title=busiest_technic_title_list,
                priority_id_list=priority_id_list
            )
            if conflict_technic_sheet:
                for conflict_ts in conflict_technic_sheet:
                    conflict_ts['total_count_apps'] = APP_TECHNIC_SERVICE.get_apps_technic_queryset(
                        isArchive=False,
                        isChecked=False,
                        technic_sheet_id__in=conflict_ts['id_list'],
                        priority=1
                    ).values_list('priority', flat=True).count()

                context['conflict_technic_sheet'] = conflict_technic_sheet
                return render(request, 'content/spec/conflicts_list.html', context)
            else:
                return HttpResponseRedirect(f'{ENDPOINTS.DASHBOARD}?current_day={current_day.date}')
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    return HttpResponseRedirect(ENDPOINTS.LOGIN)


def conflict_resolution_view(request):
    if request.user.is_authenticated:
        if USERS_SERVICE.is_administrator(request.user):
            context = {'title': 'Conflict Resolution'}

            conflict_list_id = request.GET.get('conflict_list_id')
            conflict_list_id = conflict_list_id.strip('[]').split(', ')

            current_day = WORK_DAY_SERVICE.get_current_day(request)
            context['current_day'] = current_day

            if conflict_list_id is not None and len(conflict_list_id) > 0:
                conflict_applications_technic = APP_TECHNIC_SERVICE.get_apps_technic_queryset(
                    select_related=('technic_sheet', 'application_today__construction_site__foreman'),
                    technic_sheet__in=conflict_list_id,
                    isChecked=False,
                    isArchive=False
                )
                context['applications_technic'] = conflict_applications_technic

                color_list = U.set_color_for_list(conflict_list_id)
                context['color_list'] = color_list

                technic_title = conflict_applications_technic.values_list(
                    'technic_sheet__technic__title', flat=True).first()
                context['technic_title'] = technic_title

                technic_sheets = TECHNIC_SHEET_SERVICE.get_technic_sheet_queryset(
                    select_related=('technic', 'driver_sheet__driver'),
                    isArchive=False,
                    status=True,
                    driver_sheet__isnull=False,
                    date=current_day
                )

                technic_titles_dict = TECHNIC_SERVICE.get_dict_short_technic_names(technic_sheets)
                context['technic_titles_dict'] = technic_titles_dict

                technic_driver_list = []
                for title_short, title in technic_titles_dict.items():
                    technic_driver_list.append({
                        'title_short': title_short,
                        'title': title,
                        'technic_sheets': technic_sheets.filter(technic__title=title)
                    })
                context['technic_driver_list'] = technic_driver_list

                priority_id_list = U.get_priority_id_list(technic_sheets)
                context['priority_id_list'] = priority_id_list
                busiest_technic_title_list = U.get_busiest_technic_title(technic_sheets)
                conflict_technic_sheet = U.get_conflict_list_of_technic_sheet(
                    busiest_technic_title=busiest_technic_title_list,
                    priority_id_list=priority_id_list
                )

                if conflict_technic_sheet:
                    conflict_ts = list(filter(lambda item: item['technic_title'] == technic_title,
                                              conflict_technic_sheet))
                    if conflict_ts:
                        conflict_ts = conflict_ts[0]
                        conflict_ts['total_count_apps'] = conflict_applications_technic.count()
                        context['conflict_technic_sheet'] = conflict_ts
                    else:
                        return HttpResponseRedirect(f'{ENDPOINTS.CONFLICT_LIST}?current_day={current_day.date}')
                else:
                    return HttpResponseRedirect(f'{ENDPOINTS.CONFLICT_LIST}?current_day={current_day.date}')

                if request.method == 'POST':
                    app_technic_id = request.POST.get('app_technic_id')
                    app_technic_priority = request.POST.get('app_technic_priority')

                    technic_title_short = request.POST.get('technic_title_short')
                    technic_sheet_id = request.POST.get('technic_sheet_id')
                    technic_description = request.POST.get('technic_description')

                    if U.is_valid_get_request(app_technic_priority) and U.is_valid_get_request(app_technic_id):
                        app_technic = APP_TECHNIC_SERVICE.get_app_technic(pk=app_technic_id)
                        app_technic.priority = app_technic_priority
                        app_technic.save(update_fields=['priority'])

                    if U.is_valid_get_request(technic_title_short) and U.is_valid_get_request(app_technic_id):
                        app_technic = APP_TECHNIC_SERVICE.get_app_technic(pk=app_technic_id)

                        if not U.is_valid_get_request(technic_sheet_id):
                            n_technic_title = technic_titles_dict.get(technic_title_short)
                            some_technic_sheet = TECHNIC_SHEET_SERVICE.get_some_technic_sheet(
                                technic_title=n_technic_title, workday=current_day
                            )
                        else:
                            some_technic_sheet = TECHNIC_SHEET_SERVICE.get_technic_sheet(pk=technic_sheet_id)

                        _old_ts = app_technic.technic_sheet
                        _old_ts.decrement_count_application()

                        some_technic_sheet.increment_count_application()
                        app_technic.technic_sheet = some_technic_sheet

                        if technic_description:
                            app_technic.description = technic_description
                        app_technic.save()

                # end POST =============================================================
            return render(request, 'content/spec/conflict_resolution.html', context)
    return HttpResponseRedirect(ENDPOINTS.LOGIN)


def show_technic_application(request):
    if request.user.is_authenticated:
        if USERS_SERVICE.is_administrator(request.user):
            template = 'content/applications_list/technic_application_list_for_admin.html'
        else:
            template = 'content/applications_list/technic_application_list.html'

        context = {'title': 'Заявки на технику'}

        current_day = WORK_DAY_SERVICE.get_current_day(request)
        context = U.get_prepared_data(context, current_day)
        context = U.prepare_data_for_filter(context)
        context['current_day'] = current_day

        if request.method == 'POST':
            operation = request.POST.get('operation')
            if U.is_valid_get_request(operation) and operation == 'set_props_for_filter':
                U.set_data_for_filter(request)

            app_technic_id_list = request.POST.getlist('app_technic_id')
            app_technic_priority = request.POST.getlist('app_technic_priority')
            app_technic_description = request.POST.getlist('app_technic_description')

            list_for_updates = []
            for _id, _priority, _description in zip(app_technic_id_list, app_technic_priority, app_technic_description):
                app_technic = APP_TECHNIC_SERVICE.get_app_technic(pk=_id)
                app_technic.priority = _priority
                app_technic.description = _description
                list_for_updates.append(app_technic)
            ApplicationTechnic.objects.bulk_update(objs=list_for_updates, fields=['priority', 'description'])

        application_technic_list = APP_TECHNIC_SERVICE.get_apps_technic_queryset(
            select_related=('application_today__construction_site__foreman',),
            application_today__date=current_day,
            isArchive=False,
            is_cancelled=False,
            isChecked=False
        ).exclude(application_today__status=ASSETS.SAVED)

        if not USERS_SERVICE.is_administrator(request.user):
            application_technic_list = application_technic_list.filter(application_today__status=ASSETS.SEND)

        if request.user.filter_technic:
            application_technic_list = application_technic_list.filter(
                technic_sheet__technic__title=request.user.filter_technic)
        if request.user.filter_foreman != 0:
            application_technic_list = application_technic_list.filter(
                application_today__construction_site__foreman_id=request.user.filter_foreman)
        if request.user.filter_construction_site != 0:
            application_technic_list = application_technic_list.filter(
                application_today__construction_site_id=request.user.filter_construction_site)

        technic_sheet_list = application_technic_list.values('technic_sheet').distinct()

        if request.user.sort_by == 'technic':
            technic_sheet_list = technic_sheet_list.order_by('technic_sheet__technic__title')
        elif request.user.sort_by == 'driver':
            technic_sheet_list = technic_sheet_list.order_by('technic_sheet__driver_sheet__driver__last_name')

        application_technics = []
        for technic_sheet in technic_sheet_list:
            application_technics.append({
                'technic_sheet': TECHNIC_SHEET_SERVICE.get_technic_sheet(
                    pk=technic_sheet['technic_sheet']
                ),
                'applications_list': application_technic_list.filter(
                    technic_sheet_id=technic_sheet['technic_sheet']).order_by('priority')
            })

        context['application_technics'] = application_technics

        temp_technic_sheet = TECHNIC_SHEET_SERVICE.get_technic_sheet_queryset(
            isArchive=False,
            status=True,
            driver_sheet__isnull=False,
            date=current_day
        )
        context['priority_id_list'] = U.get_priority_id_list(temp_technic_sheet)

        return render(request, template, context)
    return HttpResponseRedirect(ENDPOINTS.LOGIN)


def show_material_application(request):
    if request.user.is_authenticated:
        context = {'title': 'Materials Applications'}
        current_day = WORK_DAY_SERVICE.get_current_day(request)
        context = U.get_prepared_data(context, current_day)

        context = U.prepare_data_for_filter(context)
        context['current_day'] = current_day

        if request.method == 'POST':
            operation = request.POST.get('operation')
            if U.is_valid_get_request(operation) and operation == 'set_props_for_filter':
                U.set_data_for_filter(request)

        application_today_id_list = APP_TODAY_SERVICE.get_apps_today_queryset(
            isArchive=False,
            date=current_day,
        ).exclude(status=ASSETS.SAVED).values_list('pk', flat=True)

        if request.user.filter_foreman != 0:
            application_today_id_list = application_today_id_list.filter(
                construction_site__foreman_id=request.user.filter_foreman
            )

        if request.user.filter_construction_site != 0:
            application_today_id_list = application_today_id_list.filter(
                construction_site_id=request.user.filter_construction_site
            )

        application_materials_list = APP_MATERIAL_SERVICE.get_apps_material_queryset(
            select_related=('application_today__construction_site__foreman',),
            isArchive=False,
            application_today_id__in=application_today_id_list,
        )
        context['application_materials_list'] = application_materials_list

        return render(request, 'content/applications_list/material_application_list.html', context)
    return HttpResponseRedirect(ENDPOINTS.LOGIN)


def material_application_supply_view(request):
    if request.user.is_authenticated:
        context = {'title': 'Materials Applications'}
        _is_print = request.GET.get('print')

        current_day = WORK_DAY_SERVICE.get_current_day(request)
        context = U.get_prepared_data(context, current_day)
        context['current_day'] = current_day

        if U.is_valid_get_request(_is_print):
            application_materials_list = APP_MATERIAL_SERVICE.get_apps_material_queryset(
                select_related=('application_today__construction_site__foreman',),
                isArchive=False,
                application_today__date=current_day,
                isChecked=True
            )
            context['application_materials_list'] = application_materials_list
            context['weekday'] = ASSETS.WEEKDAY[current_day.date.weekday()]
            return render(request, 'content/spec/print_material_application.html', context)

        if request.method == 'POST':
            application_material_id = request.POST.get('application_material_id')
            application_material_description = request.POST.get('application_material_description')
            if U.is_valid_get_request(application_material_id):

                application_material = APP_MATERIAL_SERVICE.get_app_material(pk=application_material_id)

                if application_material_description != application_material.description or not application_material.isChecked:
                    application_material.description = application_material_description
                    application_material.isChecked = True
                    application_material.save()
                else:
                    application_material.isChecked = False
                    application_material.save()

        application_materials_list = APP_MATERIAL_SERVICE.get_apps_material_queryset(
            select_related=('application_today__construction_site__foreman',),
            isArchive=False,
            application_today__date=current_day
        )
        context['application_materials_list'] = application_materials_list

        return render(request, 'content/applications_list/material_application_list_for_supply.html', context)
    return HttpResponseRedirect(ENDPOINTS.LOGIN)


def profile_view(request):
    if request.user.is_authenticated:
        template = 'content/profile.html'
        context = {}

        user_id = request.GET.get('user_id')
        if user_id is not None and user_id != '':
            current_user = User.objects.get(pk=user_id)
        else:
            current_user = User.objects.get(pk=request.user.id)

        current_user_key = U.get_user_key(current_user.id)
        context['user_key'] = current_user_key

        if request.method == 'POST':
            _user_key = request.POST.get('user_key')
            if _user_key is not None and _user_key != '':
                _chat_id = U.T.get_id_chat(key=_user_key, result=U.T.get_result())
                if _chat_id:
                    current_user.telegram_id_chat = _chat_id
                    current_user.save()
                    U.send_messages_by_telegram(chat_id=_chat_id,
                                                messages='Связь установлена')

        context['current_user'] = current_user
        return render(request, template, context)

    return HttpResponseRedirect(ENDPOINTS.LOGIN)


def def_test(request):  # TODO: def TEST
    context = {}
    # _current_day = request.GET.get('current_day')
    # if _current_day:
    #     current_day = WorkDaySheet.objects.get(date=_current_day)
    # else:
    #     current_day = WorkDaySheet.objects.get(date=U.TODAY)
    # work_days = U.get_work_days().values()
    # for work_day in work_days:
    #     work_day['weekday'] = ASSETS.WEEKDAY[work_day['date'].weekday()][:3]
    template = 'content/tests/change_workday.html'
    # context = {
    #     'title': 'Test',
    #     'today': U.TODAY,
    #     'current_day': current_day,
    #     'work_days': work_days,
    #     # 'weekday': ASSETS.WEEKDAY
    # }

    # U.send_application_for_driver(current_day)
    # U.send_application_for_foreman(current_day)
    # U.send_application_for_admin(current_day)

    return render(request, template, context)


def maintenance_view(request):
    template = 'content/spec/maintenance.html'
    context = {}
    return render(request, template, context)


def settings_view(request):
    if request.user.is_authenticated:
        context = {'title': 'Параметры'}
        PARAMETER_SERVICE.prepare_global_parameters()

        if request.method == 'POST':
            PARAMETER_SERVICE.set_parameters(request.POST)
            return HttpResponseRedirect(ENDPOINTS.DASHBOARD)

        parameter_list = PARAMETER_SERVICE.get_parameter_queryset()
        context['parameter_list'] = parameter_list
        return render(request, 'content/spec/settings.html', context)

    return HttpResponseRedirect(ENDPOINTS.LOGIN)
